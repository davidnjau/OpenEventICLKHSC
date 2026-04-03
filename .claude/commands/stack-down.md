Stop all development services cleanly.

Run in order:

1. Stop the middleware (kill whatever is running on port 7000):
   ```
   kill $(lsof -ti:7000) 2>/dev/null && echo "Middleware stopped" || echo "Middleware was not running"
   ```

2. Stop the Open Event Docker stack:
   ```
   cd /Users/davidmainanjau/Documents/ICL/Development/Android/open-event/open-event-server
   docker compose down
   ```

3. Confirm nothing is left running on ports 8080, 9090, 7000, 5432.

Report what was stopped.
