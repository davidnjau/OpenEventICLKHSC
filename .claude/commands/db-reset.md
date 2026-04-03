Reset the Open Event database and re-import all KHSC delegates. Use this when the DB is in a bad state or you need a clean slate.

⚠️ This is destructive — all attendees, orders, and check-in history will be deleted. Confirm with the user before proceeding.

Steps:

1. Ask the user to confirm before continuing: "This will delete all attendees, orders, and check-in history in Open Event. Continue? (yes/no)"

2. If confirmed, delete all attendees via the OE API (requires auth token):
   - Login to get a JWT token: POST http://localhost:8080/v1/auth/login
   - Fetch all attendees for event 1: GET http://localhost:8080/v1/events/1/attendees
   - Delete each attendee: DELETE http://localhost:8080/v1/attendees/{id}

3. Re-import all KHSC delegates:
   ```
   curl -s -X POST http://localhost:7000/import \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

4. Run a diff to confirm the systems are now in sync:
   ```
   curl -s http://localhost:7000/compare/diff
   ```

5. Report how many delegates were imported and the final sync status.
