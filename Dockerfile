FROM python:3.12-slim

# Install system packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl unzip gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard] pyinfra sqlmodel

# Default command
CMD ["fastapi", "dev", "main:app"]
