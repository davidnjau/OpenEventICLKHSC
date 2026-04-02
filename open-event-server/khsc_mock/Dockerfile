FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir flask

COPY mock_server.py .
COPY delegates.json .

EXPOSE 9090

CMD ["python", "mock_server.py"]
