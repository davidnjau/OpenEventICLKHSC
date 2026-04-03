Import KHSC delegates into Open Event as attendees.

Run:
```
curl -s -X POST http://localhost:7000/import \
  -H "Content-Type: application/json" \
  -d '$ARGUMENTS'
```

If $ARGUMENTS is empty, use `{}` as the body (imports all delegates).

Examples of valid arguments:
- (no args) → imports all delegates
- `{"uids":["CONF-1001","CONF-1002"]}` → imports specific delegates
- `{"event_id":2}` → imports into a specific event

Display the result showing:
- How many delegates were created
- How many were updated
- Any that failed, with their reason

If the middleware is not running on port 7000, remind the user to start it first.
