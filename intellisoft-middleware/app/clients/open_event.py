"""
Open Event API client.

Handles JWT authentication automatically — fetches a token on first use
and refreshes it transparently when it expires (401 response).
"""

from __future__ import annotations

import threading

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenEventError(Exception):
    """Raised when the Open Event API returns an error or is unreachable."""


class OpenEventClient:
    def __init__(self) -> None:
        cfg = get_settings()
        self._base_url = cfg.open_event_base_url.rstrip("/")
        self._email = cfg.open_event_admin_email
        self._password = cfg.open_event_admin_password
        self._token: str | None = None
        self._lock = threading.Lock()

    # ── Auth ──────────────────────────────────────────────────────────────── #

    def _login(self) -> None:
        logger.info("Authenticating with Open Event as %s", self._email)
        try:
            resp = httpx.post(
                f"{self._base_url}/auth/login",
                json={"email": self._email, "password": self._password},
                timeout=10,
            )
        except httpx.RequestError as exc:
            raise OpenEventError(f"Open Event auth network error: {exc}") from exc

        if resp.status_code != 200:
            raise OpenEventError(
                f"Open Event login failed ({resp.status_code}): {resp.text}"
            )

        self._token = resp.json()["access_token"]
        logger.info("Open Event authentication successful")

    def _get_headers(self) -> dict:
        with self._lock:
            if not self._token:
                self._login()
        return {
            "Authorization": f"JWT {self._token}",
            "Content-Type":  "application/json",
        }

    # ── Internal request helpers ──────────────────────────────────────────── #

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self._base_url}/{path.lstrip('/')}"
        headers = self._get_headers()

        try:
            resp = httpx.request(method, url, headers=headers, timeout=15, **kwargs)
        except httpx.RequestError as exc:
            raise OpenEventError(f"Open Event network error [{method} {path}]: {exc}") from exc

        # Token expired — refresh once and retry
        if resp.status_code == 401:
            logger.warning("Open Event token expired — re-authenticating")
            with self._lock:
                self._token = None
                self._login()
            headers = self._get_headers()
            try:
                resp = httpx.request(method, url, headers=headers, timeout=15, **kwargs)
            except httpx.RequestError as exc:
                raise OpenEventError(f"Open Event retry error [{method} {path}]: {exc}") from exc

        logger.debug("Open Event %s %s → HTTP %s", method, path, resp.status_code)

        if resp.status_code >= 400:
            raise OpenEventError(
                f"Open Event {method} {path} failed ({resp.status_code}): {resp.text[:300]}"
            )

        if resp.status_code == 204 or not resp.content:
            return {}

        return resp.json()

    def _get(self, path: str, params: dict | None = None) -> dict:
        return self._request("GET", path, params=params)

    def _post(self, path: str, body: dict) -> dict:
        return self._request("POST", path, json=body)

    def _patch(self, path: str, body: dict) -> dict:
        return self._request("PATCH", path, json=body)

    # ── KHSC integration endpoints ────────────────────────────────────────── #

    def import_delegates(self, event_id: int, uids: list[str]) -> dict:
        """
        POST /v1/khsc/import
        Pull KHSC delegates into Open Event as attendees.
        """
        logger.info(
            "Importing %d delegate(s) into event %d via Open Event",
            len(uids), event_id,
        )
        result = self._post("/khsc/import", {"event_id": event_id, "uids": uids})
        logger.info(
            "Import result — created=%s updated=%s failed=%s",
            result.get("created"), result.get("updated"), len(result.get("failed", [])),
        )
        return result

    def sync_checkins(self, event_id: int) -> dict:
        """
        POST /v1/khsc/sync-checkins
        Reconcile check-in state between KHSC and Open Event.
        """
        logger.info("Syncing check-ins for event %d", event_id)
        result = self._post("/khsc/sync-checkins", {"event_id": event_id})
        logger.info(
            "Sync result — synced=%s already_in_sync=%s failed=%s",
            result.get("synced"), result.get("already_in_sync"), len(result.get("failed", [])),
        )
        return result

    def push_checkin(self, uid: str) -> dict:
        """
        POST /v1/khsc/push-checkin
        Push a check-in recorded in Open Event back to KHSC.
        """
        logger.info("Pushing check-in for UID %s to KHSC via Open Event", uid)
        return self._post("/khsc/push-checkin", {"uid": uid})

    # ── General Open Event API ────────────────────────────────────────────── #

    def get_events(self) -> list[dict]:
        """Return all events sorted by start date (newest first)."""
        result = self._get("/events", params={"page[size]": 0, "sort": "-starts-at"})
        return result.get("data", [])

    def get_event(self, event_id: int) -> dict:
        return self._get(f"/events/{event_id}")

    def get_attendees(self, event_id: int) -> list[dict]:
        result = self._get(
            f"/events/{event_id}/attendees",
            params={"page[size]": 0},
        )
        return result.get("data", [])

    def get_all_attendees(self, event_id: int) -> list[dict]:
        """
        Return attendees as flat dicts (JSON:API attributes unpacked),
        suitable for display and comparison.
        """
        raw = self.get_attendees(event_id)
        attendees = []
        for item in raw:
            attrs = item.get("attributes", {})
            attendees.append({
                "oe_id":         item.get("id"),
                "firstname":     attrs.get("firstname"),
                "lastname":      attrs.get("lastname"),
                "email":         attrs.get("email"),
                "company":       attrs.get("company"),
                "job_title":     attrs.get("job-title"),
                "is_checked_in": attrs.get("is-checked-in"),
                "checkin_times": attrs.get("checkin-times"),
                "identifier":    attrs.get("identifier"),
            })
        return attendees

    def get_event_stats(self, event_id: int) -> dict:
        return self._get(f"/events/{event_id}/general-statistics")
