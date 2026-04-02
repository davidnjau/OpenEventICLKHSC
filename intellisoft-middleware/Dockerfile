FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

EXPOSE 7000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000", "--log-level", "warning"]
