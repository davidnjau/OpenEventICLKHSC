# KHSC Mock Server

Local simulation of `https://khsc.site/api/index.php` for development without production credentials.

## Start the Mock Server

```bash
pip install flask
python khsc_mock/mock_server.py
```

Server runs at: `http://localhost:9090/api/index.php`

---

## Dummy Credentials

Use these headers on every request:

| Header | Value |
|---|---|
| `X-API-Username` | `admin_desk_1` |
| `Authorization` | `Bearer tok_test_khsc_mock_2026` |
| `X-Pass-Key` | `pk_test_khsc_mock_2026` |
| `X-Secret-Key` | `sk_test_khsc_mock_2026` |

---

## Dummy Delegates

| UID | Name | Organization | Payment | Checked In |
|---|---|---|---|---|
| CONF-1001 | James Mwangi | Kenyatta National Hospital | Paid | No |
| CONF-1002 | Aisha Mohamed | Ministry of Health | Paid | No |
| CONF-1003 | Peter Otieno | University of Nairobi | Paid | No |
| CONF-1004 | Grace Wanjiku | Kenya Medical Training College | Paid | No |
| CONF-1005 | David Kipchoge | KEMSA | **Unpaid** | No |
| CONF-1006 | Fatuma Hassan | Coast General Hospital | Paid | No |
| CONF-1007 | Brian Ndegwa | Aga Khan University Hospital | Paid | **Yes** |
| CONF-1008 | Caroline Njeri | University of Nairobi | **Unpaid** | No |
| CONF-1009 | Samuel Koech | Moi Teaching & Referral Hospital | Paid | No |
| CONF-1010 | Lydia Mutua | KEMRI | Paid | No |
| CONF-1011 | Ahmed Omar | Kenyatta University Teaching Hospital | **Unpaid** | No |
| CONF-1012 | Mercy Achieng | World Health Organization | Paid | No |

State is **persisted** in `delegates.json` across requests. To reset, restore the original file from git.

---

## Endpoints

### Verify Delegate
```
GET /api/index.php?endpoint=verify_delegate&uid=CONF-1001
```

### Check In
```
POST /api/index.php?endpoint=check_in
{"uid": "CONF-1001"}
```

### Search Delegate
```
GET /api/index.php?endpoint=search_delegate&q=mwangi
GET /api/index.php?endpoint=search_delegate&q=kemri
GET /api/index.php?endpoint=search_delegate&q=CONF-100
```

### Offline Bulk Sync
```
POST /api/index.php?endpoint=offline_sync
{"uids": ["CONF-1003", "CONF-1004", "CONF-1005"]}
```

### Mark Paid On-Site
```
POST /api/index.php?endpoint=mark_paid_onsite
{"uid": "CONF-1005", "payment_method": "On-Site Cash"}

POST /api/index.php?endpoint=mark_paid_onsite
{"uid": "CONF-1008", "payment_method": "On-Site PDQ Card"}
```

### Live Event Stats
```
GET /api/index.php?endpoint=event_stats
```

### Sandbox Test
```
POST /api/index.php?endpoint=sandbox_test
```

---

## Run All Tests

```bash
# Terminal 1 — start mock server
python khsc_mock/mock_server.py

# Terminal 2 — run test suite
python khsc_mock/test_endpoints.py
```

## Reset Delegate State

```bash
git checkout khsc_mock/delegates.json
```
