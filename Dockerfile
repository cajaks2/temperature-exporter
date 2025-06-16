FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    digitemp \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy app
COPY temperature_exporter.py /app/

# Install Python packages
RUN pip install flask prometheus_client python-json-logger gunicorn

# Expose port
EXPOSE 9012

# Run with Gunicorn and structured JSON logs
CMD ["gunicorn", "-b", "0.0.0.0:9012", "temperature_exporter:app", \
     "--access-logformat", "{\"time\": \"%(t)s\", \"status\": \"%(s)s\", \"method\": \"%(m)s\", \"path\": \"%(U)s\", \"remote_addr\": \"%(h)s\"}", \
     "--access-logfile", "-", "--error-logfile", "-"]
