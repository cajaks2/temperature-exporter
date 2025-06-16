# Temperature Exporter

A Prometheus-compatible exporter that reads temperature from DS18B20 1-Wire sensors using `digitemp_DS9097`. Designed for use in Docker or Kubernetes, with structured logging, JSON output, and health checks.

## Features

- Prometheus `/metrics` endpoint  
- `/json` endpoint for structured temperature data  
- `/healthz` endpoint for Kubernetes readiness/liveness  
- JSON logging via `python-json-logger`  
- Production-ready with Gunicorn  
- Compatible with `/dev/ttyUSB0` via hostPath or device pass-through  

## Endpoints

| Path       | Description                          |
|------------|--------------------------------------|
| `/metrics` | Prometheus scrape metrics            |
| `/json`    | Latest temperature reading as JSON   |
| `/healthz` | Returns 200 if sensor is readable    |

## Example Output

### `/json`

```json
{
  "sensor_id": 0,
  "temperature_celsius": 23.56,
  "temperature_fahrenheit": 74.41,
  "location": "closet"
}
```

### `/metrics`

```
# HELP serial_temperature_celsius Temperature in Celsius
# TYPE serial_temperature_celsius gauge
serial_temperature_celsius{location="closet"} 23.56
# HELP serial_temperature_fahrenheit Temperature in Fahrenheit
# TYPE serial_temperature_fahrenheit gauge
serial_temperature_fahrenheit{location="closet"} 74.41
```

## digitemp.conf Example

```text
TTY /dev/ttyUSB0
READ_TIME 1000
LOG_TYPE 1
LOG_FORMAT "%b %d %H:%M:%S Sensor %s C: %.2C F: %.2F"
CNT_FORMAT "%b %d %H:%M:%S Sensor %s #%n %C"
HUM_FORMAT "%b %d %H:%M:%S Sensor %s C: %.2C F: %.2F H: %h%%"
SENSORS 1
ROM 0 0x28 0xFF 0xC2 0x9C 0x31 0x18 0x02 0x49
```

## Docker

### Build

```bash
docker build -t temperature-exporter .
```

### Run

```bash
docker run --device=/dev/ttyUSB0 \
  -v /etc/digitemp.conf:/etc/digitemp.conf \
  -p 9012:9012 \
  cooperjackson/temperature-exporter:latest
```

## Kubernetes Highlights

- Uses `hostPort: 9012`
- Targets a specific node via `kubernetes.io/hostname: remote-desktop`
- Mounts device via hostPath (`/dev/ttyUSB0`)
- Loads `digitemp.conf` via ConfigMap
- Uses `Recreate` strategy to avoid hardware race conditions
- Includes health and readiness probes on `/healthz`
- `imagePullPolicy: Always` to always fetch latest version

### Label node if needed:

```bash
kubectl label node remote-desktop kubernetes.io/hostname=remote-desktop
```

