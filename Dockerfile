FROM python:3.11-slim

# Install git (required for cloning repos) and gcc (for some python packages)
RUN apt-get update && apt-get install -y git gcc libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure the python path includes /app
ENV PYTHONPATH=/app
