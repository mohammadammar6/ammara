FROM python:3.11-slim

WORKDIR /app

# Install build deps and runtime deps
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev build-essential && \
    pip install --no-cache-dir -r requirements.txt gunicorn && \
    apt-get remove -y gcc build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 5000

# Use Gunicorn and call factory `create_app()` from app.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
