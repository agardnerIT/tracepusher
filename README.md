# OpenTelemetry TracePusher

Generate and push dummy OpenTelemetry Trace data to an endpoint in JSON format

# Requirements and Prequisites
- A running OpenTelemetry collector (see below)
- Requires `requests` module (`pip install -r requirements.txt`)

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

## Spin up OpenTelemetry Collector

## Download Collector
Download and extract the collector binary for your platform from here.

For example, for windows: `https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.70.0/otelcol-contrib_0.70.0_windows_amd64.tar.gz`

Unzip and extract so you have the binary (eg. `otelcol.exe`)

## Create config.yaml
The OpenTelemetry collector needs a config file - this is how you decide which trace backend the traces will go to.

Save this file alongside `otelcol.exe` as `config.yaml`.

You will need to modify the `otlphttp` code for your backend. The example gives is for Dynatrace trace ingest.
For Dynatrace, the API token needs `Ingest OpenTelemetry traces` permissions.

```
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:
    send_batch_max_size: 1000
    timeout: 30s
    send_batch_size : 800

  memory_limiter:
    check_interval: 1s
    limit_percentage: 70
    spike_limit_percentage: 30

exporters:
  logging:
    verbosity: detailed

  otlphttp:
    endpoint: https://abc12345.live.dynatrace.com/api/v2/otlp
    headers:
      Authorization: "Api-Token dt0c01.sample.secret"

service:
  extensions: []
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlphttp,logging]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter,batch]
      exporters: [otlphttp]
```

## Start The Collector

Open a command / terminal window and run:

```
otelcol.exe --config config.yaml
```
