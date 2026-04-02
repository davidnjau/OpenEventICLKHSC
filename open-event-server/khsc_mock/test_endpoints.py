"""
KHSC Mock API — Test Script
Exercises all 7 endpoints against the local mock server.

Usage:
    # Start mock server first:
    python khsc_mock/mock_server.py

    # Then in a separate terminal:
    python khsc_mock/test_endpoints.py
"""

import requests
import json

BASE_URL = "http://localhost:9090/api/index.php"

# Dummy credentials matching mock_server.py
HEADERS = {
    "Content-Type":  "application/json",
    "X-API-Username": "admin_desk_1",
    "Authorization":  "Bearer tok_test_khsc_mock_2026",
    "X-Pass-Key":     "pk_test_khsc_mock_2026",
    "X-Secret-Key":   "sk_test_khsc_mock_2026",
}

def print_result(title, response):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"  Status: {response.status_code}")
    print(f"  Response:")
    print(json.dumps(response.json(), indent=4))

# ---------------------------------------------------------------------------
# 1. Verify a PAID delegate (expect: can_enter = true)
# ---------------------------------------------------------------------------
r = requests.get(
    BASE_URL,
    params={"endpoint": "verify_delegate", "uid": "CONF-1001"},
    headers=HEADERS
)
print_result("1. Verify Delegate — Paid (CONF-1001)", r)

# ---------------------------------------------------------------------------
# 2. Verify an UNPAID delegate (expect: can_enter = false)
# ---------------------------------------------------------------------------
r = requests.get(
    BASE_URL,
    params={"endpoint": "verify_delegate", "uid": "CONF-1005"},
    headers=HEADERS
)
print_result("2. Verify Delegate — Unpaid (CONF-1005)", r)

# ---------------------------------------------------------------------------
# 3. Verify a NON-EXISTENT delegate (expect: 404)
# ---------------------------------------------------------------------------
r = requests.get(
    BASE_URL,
    params={"endpoint": "verify_delegate", "uid": "CONF-9999"},
    headers=HEADERS
)
print_result("3. Verify Delegate — Not Found (CONF-9999)", r)

# ---------------------------------------------------------------------------
# 4. Check in a paid delegate (expect: success)
# ---------------------------------------------------------------------------
r = requests.post(
    BASE_URL,
    params={"endpoint": "check_in"},
    headers=HEADERS,
    json={"uid": "CONF-1002"}
)
print_result("4. Check-In — Paid Delegate (CONF-1002)", r)

# ---------------------------------------------------------------------------
# 5. Check in the same delegate again (expect: already checked in error)
# ---------------------------------------------------------------------------
r = requests.post(
    BASE_URL,
    params={"endpoint": "check_in"},
    headers=HEADERS,
    json={"uid": "CONF-1002"}
)
print_result("5. Check-In — Already Checked In (CONF-1002)", r)

# ---------------------------------------------------------------------------
# 6. Check in an UNPAID delegate (expect: denied)
# ---------------------------------------------------------------------------
r = requests.post(
    BASE_URL,
    params={"endpoint": "check_in"},
    headers=HEADERS,
    json={"uid": "CONF-1005"}
)
print_result("6. Check-In — Unpaid Delegate (CONF-1005)", r)

# ---------------------------------------------------------------------------
# 7. Search delegate by last name
# ---------------------------------------------------------------------------
r = requests.get(
    BASE_URL,
    params={"endpoint": "search_delegate", "q": "mwangi"},
    headers=HEADERS
)
print_result("7. Search Delegate — 'mwangi'", r)

# ---------------------------------------------------------------------------
# 8. Search delegate by organization
# ---------------------------------------------------------------------------
r = requests.get(
    BASE_URL,
    params={"endpoint": "search_delegate", "q": "kemri"},
    headers=HEADERS
)
print_result("8. Search Delegate — 'kemri'", r)

# ---------------------------------------------------------------------------
# 9. Offline bulk sync (mix of valid, unpaid, not-found)
# ---------------------------------------------------------------------------
r = requests.post(
    BASE_URL,
    params={"endpoint": "offline_sync"},
    headers=HEADERS,
    json={"uids": ["CONF-1003", "CONF-1004", "CONF-1005", "CONF-9999"]}
)
print_result("9. Offline Sync — Mixed batch", r)

# ---------------------------------------------------------------------------
# 10. Mark unpaid delegate as paid on-site (cash)
# ---------------------------------------------------------------------------
r = requests.post(
    BASE_URL,
    params={"endpoint": "mark_paid_onsite"},
    headers=HEADERS,
    json={"uid": "CONF-1008", "payment_method": "On-Site Cash"}
)
print_result("10. Mark Paid On-Site — Cash (CONF-1008)", r)

# ---------------------------------------------------------------------------
# 11. Mark on-site with PDQ/card
# ---------------------------------------------------------------------------
r = requests.post(
    BASE_URL,
    params={"endpoint": "mark_paid_onsite"},
    headers=HEADERS,
    json={"uid": "CONF-1011", "payment_method": "On-Site PDQ Card"}
)
print_result("11. Mark Paid On-Site — PDQ Card (CONF-1011)", r)

# ---------------------------------------------------------------------------
# 12. Attempt to mark already-paid delegate as paid (expect: conflict)
# ---------------------------------------------------------------------------
r = requests.post(
    BASE_URL,
    params={"endpoint": "mark_paid_onsite"},
    headers=HEADERS,
    json={"uid": "CONF-1001", "payment_method": "On-Site Cash"}
)
print_result("12. Mark Paid On-Site — Already Paid (CONF-1001)", r)

# ---------------------------------------------------------------------------
# 13. Event dashboard stats (reflects all mutations above)
# ---------------------------------------------------------------------------
r = requests.get(
    BASE_URL,
    params={"endpoint": "event_stats"},
    headers=HEADERS
)
print_result("13. Live Event Stats", r)

# ---------------------------------------------------------------------------
# 14. Sandbox test / request live keys
# ---------------------------------------------------------------------------
r = requests.post(
    BASE_URL,
    params={"endpoint": "sandbox_test"},
    headers=HEADERS
)
print_result("14. Sandbox Test", r)

# ---------------------------------------------------------------------------
# 15. Bad credentials (expect: 401)
# ---------------------------------------------------------------------------
bad_headers = {**HEADERS, "X-Secret-Key": "wrong_key"}
r = requests.get(
    BASE_URL,
    params={"endpoint": "event_stats"},
    headers=bad_headers
)
print_result("15. Bad Credentials (expect 401)", r)

print(f"\n{'='*60}")
print("  All tests complete.")
print(f"{'='*60}\n")
