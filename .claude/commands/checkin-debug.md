Debug a check-in issue for a specific delegate or across the whole event.

Usage:
- `/checkin-debug`              → show overall check-in state for all events
- `/checkin-debug CONF-1001`    → debug a specific KHSC UID
- `/checkin-debug <attendee_id>` → debug a specific Open Event attendee ID

Steps:

1. Get an auth token:
   ```
   TOKEN=$(curl -s -X POST http://localhost:8080/auth/session \
     -H 'Content-Type: application/json' \
     -d '{"email":"$ADMIN_EMAIL","password":"$ADMIN_PASSWORD"}' \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
   ```
   Use the credentials from the root `.env` file.

2. If $ARGUMENTS looks like `CONF-XXXX` (KHSC UID):
   a. Check KHSC mock:
      ```
      curl -s "http://localhost:9090/api/index.php?endpoint=verify_delegate&uid=$ARGUMENTS" \
        -H "X-API-Username: admin_desk_1" \
        -H "Authorization: Bearer tok_test_khsc_mock_2026" \
        -H "X-Pass-Key: pk_test_khsc_mock_2026" \
        -H "X-Secret-Key: sk_test_khsc_mock_2026"
      ```
   b. Check Open Event (search by khsc_uid via middleware diff):
      ```
      curl -s "http://localhost:7000/compare/diff" | python3 -c "
      import sys, json
      d = json.load(sys.stdin)
      uid = '$ARGUMENTS'
      for item in d.get('mismatches', []) + d.get('only_in_khsc', []):
          if item.get('uid') == uid: print(json.dumps(item, indent=2))
      "
      ```
   c. Report: KHSC state vs OE state, whether they match, suggested fix.

3. If $ARGUMENTS is empty — show a summary table:
   - Total attendees in OE with check-in = true
   - Total delegates in KHSC with is_checked_in = true
   - Any mismatch count from `/compare/diff`

4. Suggest remediation:
   - State mismatch → run `/sync`
   - Delegate missing from OE → run `/import {"uids":["$ARGUMENTS"]}`
   - Check-in time missing but is_checked_in = true → data integrity issue, show attendee record
