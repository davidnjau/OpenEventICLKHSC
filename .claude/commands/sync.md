Reconcile check-in state between KHSC and Open Event. KHSC is the source of truth.

Run:
```
curl -s -X POST http://localhost:7000/sync/checkins \
  -H "Content-Type: application/json" \
  -d '{}'
```

Display the result showing:
- How many attendees were synced (check-in state updated)
- How many were already in sync
- Any failures

Then run the diff to confirm both systems are now aligned:
```
curl -s http://localhost:7000/compare/diff
```

Show the summary line from the diff response.
