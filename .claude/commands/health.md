Check the health of all running services in this project.

Run the following steps in order:

1. Hit the middleware health endpoint:
   `curl -s http://localhost:7000/health`
   Parse and display the result showing status of KHSC API and Open Event API.

2. If the middleware is not running (connection refused on 7000), say so clearly.

3. Also check if the Open Event server is directly reachable:
   `curl -s http://localhost:8080/v1/events`

4. Check Docker containers are running:
   `docker ps --format "{{.Names}}\t{{.Status}}" | grep opev`

5. Summarise overall system status as: HEALTHY / DEGRADED / DOWN, and list any services that are not reachable.
