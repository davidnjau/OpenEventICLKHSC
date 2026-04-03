Compare KHSC delegates against Open Event attendees and report any mismatches.

Run:
```
curl -s http://localhost:7000/compare/diff
```

Display a clear, readable report:

1. **Summary line** — total in each system, how many matched, how many are in sync
2. **Only in KHSC** — delegates not yet imported into Open Event (list their uid, name, email)
3. **Only in Open Event** — attendees with no matching KHSC delegate (orphaned records)
4. **Field mismatches** — matched records where data differs (show uid, field name, KHSC value vs OE value)

If everything is in sync, say so clearly. If there are issues, suggest the appropriate fix:
- "Only in KHSC" → run `/import` to bring them in
- "Only in OE" → investigate manually (should not happen in normal flow)
- "Field mismatches" → run `/sync` to reconcile check-in state, or re-import for data mismatches
