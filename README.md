# OpenTelemetry TracePusher

Generate and push OpenTelemetry Trace data to an endpoint in JSON format.

![architecture](assets/architecture.png)
![trace](assets/trace.png)

# Requirements and Prequisites
- A running OpenTelemetry collector (see below)
- Requires `requests` module (`pip install -r requirements.txt`)

# Usage

`python tracepusher.py -h` or `python tracepusher.py --help` shows help text.

```
python tracepusher.py http(s)://OTEL-COLLECTOR-ENDPOINT:4318 service_name span_name SPAN_TIME_IN_SECONDS
eg. python tracepusher.py http://localhost:4318 tracepusher my-span 2
```

or:

```
docker run gardnera/tracepusher:v0.3.1 http(s)://OTEL-COLLECTOR-ENDPOINT:4318 service_name span_name SPAN_TIME_IN_SECONDS
```

## Dry Run Mode
Add `--dry` or `--dry-run` mode to run without actually pushing any data.

## Debug Mode
Add `-d` or `--debug` for extra output

## Time Shifting
In "default mode" tracepusher starts a trace `now` and finishes it `SPAN_TIME_IN_SECONDS` in the future.
You may want to push timings for traces that have already occurred (eg. shell scripts). See https://github.com/agardnerIT/tracepusher/issues/4.

If `--shift` is added as the final parameter, `start` and `end` times will be shifted back by `SPAN_TIME_IN_SECONDS`.

## Spin up OpenTelemetry Collector

## Download Collector
The Python script will generate and push a trace to an OpenTelemetry collector. So of course, you need one available.

If you have a collector already available, go on ahead to run the tool. If you **don't** have one already available, follow these steps.

Download and extract the collector binary for your platform from [here](https://github.com/open-telemetry/opentelemetry-collector-releases/releases/tag/v0.71.0).

For example, for windows: `https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.71.0/otelcol-contrib_0.70.0_windows_amd64.tar.gz`

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
python tracepusher.py http://localhost:4318 tracepusher my-span 2
```

----------------------

# FAQs

## Why Does This Exist?
Why, when [tracegen](https://www.jaegertracing.io/docs/1.42/tools/) and the replacement [telemetrygen](https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/9597) exist, does this exist?

This tool does not replace or supercede those tools in any way. For lots of usecases and people, those tools will be better.

However, they hide the inner-workings (the *how*). For someone getting started or wanting to truly understand what is happening, there is "too much magic". Stuff "just works" whereas tracepusher is more explicit - and thus (I believe) easier to see how the pieces fit together.

The trace data that tracepusher generates is also customisable whereas "you get what you get" with `tracegen / telemetrygen`.

----------------------

# Contributing

All contributions are most welcome! Create an issue or a PR and see your name here!

<a href="https://github.com/agardnerit/tracepusher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=agardnerit/tracepusher" />
</a>

Made with [contrib.rocks](https://contrib.rocks).
