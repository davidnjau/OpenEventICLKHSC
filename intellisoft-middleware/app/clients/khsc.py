"""
KHSC API client.

All four required auth headers are injected automatically on every request.
Raises KHSCError for any non-2xx response or network failure.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class KHSCError(Exception):
    """Raised when the KHSC API returns an error or is unreachable."""


class KHSCClient:
    def __init__(self) -> None:
        cfg = get_settings()
        self._base_url = cfg.khsc_api_url
        self._headers = {
            "X-API-Username":  cfg.khsc_api_username,
            "Authorization":   cfg.khsc_authorization,
            "X-Pass-Key":      cfg.khsc_pass_key,
            "X-Secret-Key":    cfg.khsc_secret_key,
            "Content-Type":    "application/json",
        }

    # ── Internal request helper ───────────────────────────────────────────── #

    def _get(self, params: dict) -> dict:
        endpoint = params.get("endpoint", "?")
        try:
            resp = httpx.get(self._base_url, headers=self._headers, params=params, timeout=10)
            logger.debug("KHSC GET %s → HTTP %s", endpoint, resp.status_code)
            data = resp.json()
        except httpx.RequestError as exc:
            raise KHSCError(f"KHSC network error on {endpoint}: {exc}") from exc

        if resp.status_code >= 400 or data.get("status") != "success":
            msg = data.get("message", resp.text)
            raise KHSCError(f"KHSC {endpoint} failed ({resp.status_code}): {msg}")

        return data

    def _post(self, params: dict, body: dict) -> dict:
        endpoint = params.get("endpoint", "?")
        try:
            resp = httpx.post(
                self._base_url,
                headers=self._headers,
                params=params,
                json=body,
                timeout=10,
            )
            logger.debug("KHSC POST %s → HTTP %s", endpoint, resp.status_code)
            data = resp.json()
        except httpx.RequestError as exc:
            raise KHSCError(f"KHSC network error on {endpoint}: {exc}") from exc

        if resp.status_code >= 400 or data.get("status") != "success":
            msg = data.get("message", resp.text)
            raise KHSCError(f"KHSC {endpoint} failed ({resp.status_code}): {msg}")

        return data

    # ── Public API methods ────────────────────────────────────────────────── #

    def verify_delegate(self, uid: str) -> dict:
        """Fetch a single delegate's details from KHSC."""
        logger.debug("Verifying delegate %s", uid)
        result = self._get({"endpoint": "verify_delegate", "uid": uid})
        return result["data"]

    def check_in(self, uid: str) -> dict:
        """Record a check-in for a delegate in KHSC."""
        logger.info("Pushing check-in to KHSC for %s", uid)
        result = self._post({"endpoint": "check_in"}, {"uid": uid})
        return result.get("data", {})

    def search_delegates(self, query: str) -> list[dict]:
        """Search delegates by name, email, organization, or UID."""
        logger.debug("Searching KHSC delegates: %r", query)
        result = self._get({"endpoint": "search_delegate", "q": query})
        return result.get("data", [])

    def offline_sync(self, uids: list[str]) -> dict:
        """Bulk check-in multiple delegates (offline sync mode)."""
        logger.info("KHSC offline sync for %d UIDs", len(uids))
        result = self._post({"endpoint": "offline_sync"}, {"uids": uids})
        return result.get("data", {})

    def mark_paid_onsite(self, uid: str, payment_method: str = "On-Site Cash") -> dict:
        """Mark a delegate as paid on-site."""
        logger.info("Marking %s as paid on-site via %s", uid, payment_method)
        result = self._post(
            {"endpoint": "mark_paid_onsite"},
            {"uid": uid, "payment_method": payment_method},
        )
        return result.get("data", {})

    def get_event_stats(self) -> dict:
        """Fetch live event statistics from KHSC."""
        result = self._get({"endpoint": "event_stats"})
        return result.get("data", {})

    def get_all_delegates(self) -> list[dict]:
        """Fetch every delegate registered in KHSC."""
        return self.search_delegates("CONF-")

    def sandbox_test(self) -> dict:
        """Test connectivity against KHSC sandbox."""
        result = self._post({"endpoint": "sandbox_test"}, {})
        return result.get("data", {})
