# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the whole project
COPY . .

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install fastapi[all] pyinfra sqlmodel httpx

# Expose the FastAPI dev port
EXPOSE 8000

# Run the FastAPI dev server
CMD ["fastapi", "dev", "main:app"]
