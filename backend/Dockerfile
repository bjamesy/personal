FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer — only re-runs when pyproject.toml changes)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Install Playwright browser + system dependencies
RUN playwright install chromium --with-deps

# Copy source (overridden by volume mount in dev, used as-is in prod)
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
