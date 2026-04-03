Start the full development stack for this project.

Run these steps in order:

1. Start the Open Event stack (server, postgres, redis, KHSC mock):
   ```
   cd /Users/davidmainanjau/Documents/ICL/Development/Android/open-event/open-event-server
   docker compose up -d
   ```

2. Wait for the web container to be healthy, then verify:
   ```
   curl -s http://localhost:8080/v1/events
   ```

3. Start the Intellisoft middleware (load env from .env file):
   ```
   cd /Users/davidmainanjau/Documents/ICL/Development/Android/open-event/intellisoft-middleware
   ```
   Load variables from the .env file and start uvicorn on port 7000 with --reload.

4. Verify the middleware is up:
   ```
   curl -s http://localhost:7000/health
   ```

5. Report the status of each service:
   - Open Event server: http://localhost:8080
   - KHSC mock: http://localhost:9090
   - Middleware: http://localhost:7000
   - Swagger docs: http://localhost:7000/docs

If any service fails to start, show the error and suggest a fix.
