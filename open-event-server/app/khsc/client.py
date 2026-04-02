"""
KHSC HTTP client.

Reads all credentials from the environment (set via root .env / setup.py).
All other integration code goes through this class — nothing else should know
how KHSC authentication works.

Environment variables (all required):
    KHSC_API_URL        e.g. http://localhost:9090/api/index.php  (mock)
                            or https://khsc.site/api/index.php   (production)
    KHSC_API_USERNAME
    KHSC_AUTHORIZATION  full value including "Bearer " prefix
    KHSC_PASS_KEY
    KHSC_SECRET_KEY
"""

import os

import requests


class KHSCError(Exception):
    """Raised when KHSC returns a non-success status or an HTTP error."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class KHSCClient:
    def __init__(self):
        self.base_url = os.environ.get('KHSC_API_URL', '').rstrip('/')
        self.headers = {
            'Content-Type':   'application/json',
            'X-API-Username': os.environ.get('KHSC_API_USERNAME', ''),
            'Authorization':  os.environ.get('KHSC_AUTHORIZATION', ''),
            'X-Pass-Key':     os.environ.get('KHSC_PASS_KEY', ''),
            'X-Secret-Key':   os.environ.get('KHSC_SECRET_KEY', ''),
        }
        if not self.base_url:
            raise KHSCError('KHSC_API_URL is not set in the environment.')

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get(self, endpoint, **params):
        params['endpoint'] = endpoint
        resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
        return self._unwrap(resp)

    def _post(self, endpoint, body):
        resp = requests.post(
            self.base_url,
            headers=self.headers,
            params={'endpoint': endpoint},
            json=body,
            timeout=10,
        )
        return self._unwrap(resp)

    @staticmethod
    def _unwrap(resp):
        try:
            payload = resp.json()
        except Exception:
            raise KHSCError(f'Non-JSON response from KHSC ({resp.status_code})', resp.status_code)

        if resp.status_code not in (200, 201):
            msg = payload.get('message', resp.text)
            raise KHSCError(msg, resp.status_code)

        if payload.get('status') != 'success':
            raise KHSCError(payload.get('message', 'Unknown KHSC error'), resp.status_code)

        return payload

    # ── Public API methods ────────────────────────────────────────────────────

    def verify_delegate(self, uid):
        """
        Look up a single delegate by UID.
        Returns the 'data' dict including can_enter, payment_status, is_checked_in.
        """
        return self._get('verify_delegate', uid=uid)['data']

    def check_in(self, uid):
        """
        Mark a delegate as checked in on the KHSC side.
        Raises KHSCError(403) if unpaid, KHSCError(409) if already checked in.
        """
        return self._post('check_in', {'uid': uid})['data']

    def search(self, query):
        """
        Search delegates by name, email, organisation, or UID fragment.
        Returns a list of delegate dicts.
        """
        return self._get('search_delegate', q=query)['data']

    def offline_sync(self, uids):
        """
        Bulk check-in for delegates recorded offline.
        Returns {'successful': int, 'failed': [{'uid', 'reason'}]}.
        """
        return self._post('offline_sync', {'uids': uids})['data']

    def mark_paid_onsite(self, uid, payment_method='On-Site Cash'):
        """
        Settle an on-site payment for an unpaid delegate.
        """
        return self._post('mark_paid_onsite', {'uid': uid, 'payment_method': payment_method})['data']

    def event_stats(self):
        """
        Live event totals: registered, paid, checked_in, unpaid, revenue.
        """
        return self._get('event_stats')['data']
