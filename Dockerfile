# Uses the official Playwright Python image which has Chromium
# and all system dependencies pre-installed.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Playwright browsers match our installed version
RUN playwright install chromium

# Copy application code
COPY . .

# Render injects $PORT — must bind to 0.0.0.0
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT"]
