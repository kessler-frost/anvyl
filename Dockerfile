# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set working directory
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY README.md .

ENV PYTHONPATH=/app

CMD ["python", "-m", "fastapi", "run", "src/sindri/main.py", "--host", "0.0.0.0", "--port", "8000"]
