This page shows sample configuration and instructions for creating an OpenTelemetry Collector.

Specifically, the `config.yaml` shows how to send traces to Dynatrace as a backend.

If you need Dynatrace tenant, [click here to signup for a free trial](https://dynatrace.com/trial).

## Download Collector

The Python script will generate and push a trace to an OpenTelemetry collector. So of course, you need one available.

If you have a collector already available, go on ahead to run the tool. If you **don't** have one already available, follow these steps.

Download and extract the collector binary for your platform from [here](https://github.com/open-telemetry/opentelemetry-collector-releases/releases/tag/v0.78.0).

For example, for windows: `https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.78.0/otelcol-contrib_0.78.0_windows_amd64.tar.gz`

Unzip and extract so you have the binary (eg. `otelcol.exe`)

## Create config.yaml

The OpenTelemetry collector needs a config file - this is how you decide which trace backend the traces will go to.

Save this file alongside `otelcol.exe` as `config.yaml`.

You will need to modify the `otlphttp` code for your backend. The example given is for Dynatrace trace ingest.
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

Then run tracepusher:

```
python tracepusher.py --endpoint http://localhost:4318 --service-name tracepusher --span-name my-span --duration 2
```
