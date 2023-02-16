# OpenTelemetry TracePusher

Generate and push dummy OpenTelemetry Trace data to an endpoint in JSON format

# Requirements
Requires `requests` module (`pip install -r requirements.txt`)

# Usage

`python tracepusher.py -h` or `python tracepusher.py --help` shows help text.

```
Usage: python tracepusher.py http://OTEL-COLLECTOR-ENDPOINT:4318 service_name span_name SPAN_TIME_IN_SECONDS
eg. python tracepusher.py http://localhost:4318 tracepusher my-span 2
```

## Dry Run Mode
Add `--dry` or `--dry-run` mode to run without actually pushing any data.

## Debug Mode
Add `-d` or `--debug` for extra output
