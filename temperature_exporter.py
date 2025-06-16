from flask import Flask, Response
import subprocess
import logging
import json
import re
from prometheus_client import Gauge, generate_latest
from pythonjsonlogger import jsonlogger

# Setup JSON logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Initialize Flask app
app = Flask("temperature_exporter")

# Prometheus metrics
temperature_celsius = Gauge('serial_temperature_celsius', 'Temperature in Celsius', ['location'])
temperature_fahrenheit = Gauge('serial_temperature_fahrenheit', 'Temperature in Fahrenheit', ['location'])

def read_temperature():
    """Run digitemp and parse the output into JSON."""
    try:
        result = subprocess.run(
            ["/usr/bin/digitemp_DS9097", "-a", "-q", "-c", "/etc/digitemp.conf"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error({"error": "digitemp execution failed", "details": e.stderr.strip()})
        raise RuntimeError(f"digitemp failed: {e.stderr.strip()}")

    for line in result.stdout.strip().splitlines():
        match = re.search(r'Sensor\s+(\d+)\s+C:\s+([-+]?[0-9]*\.?[0-9]+)\s+F:\s+([-+]?[0-9]*\.?[0-9]+)', line)
        if match:
            sensor_id = int(match.group(1))
            celsius = float(match.group(2))
            fahrenheit = float(match.group(3))
            logger.info({"sensor_id": sensor_id, "celsius": celsius, "fahrenheit": fahrenheit})
            return json.dumps({
                "sensor_id": sensor_id,
                "temperature_celsius": celsius,
                "temperature_fahrenheit": fahrenheit,
                "location": "closet"
            })

    logger.error({"error": "No valid temperature data found"})
    raise RuntimeError("No valid sensor reading found.")

@app.route('/metrics')
def metrics():
    try:
        parsed = json.loads(read_temperature())
        temperature_celsius.labels(location=parsed['location']).set(parsed['temperature_celsius'])
        temperature_fahrenheit.labels(location=parsed['location']).set(parsed['temperature_fahrenheit'])
    except Exception as e:
        logger.error({"error": "Failed to update Prometheus metrics", "details": str(e)})
        return Response(f"Error: {e}", status=500)
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/healthz')
def healthz():
    try:
        _ = json.loads(read_temperature())  # Just test the device works
        return Response("ok", status=200)
    except Exception as e:
        logger.error({"error": "Health check failed", "details": str(e)})
        return Response("unhealthy", status=500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9012)
