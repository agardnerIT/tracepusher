# OpenTelemetry TracePusher

Generate and push OpenTelemetry Trace data to an endpoint in JSON format.

![architecture](assets/architecture.png)
![trace](assets/trace.png)

# Requirements and Prequisites
- A running OpenTelemetry collector (see below)
- Requires `requests` module (`pip install -r requirements.txt`)
- Requires Python 3 or docker.

## Python3 Usage

`python3 tracepusher.py -h` or `python3 tracepusher.py --help` shows help text.

```
python tracepusher.py \
--endpoint=http(s)://OTEL-COLLECTOR-ENDPOINT:4318
--service-name=service_name \
--span-name=spanA \
--duration=2
```

## Docker Usage

```
docker run gardnera/tracepusher:v0.5.0 \
-ep=http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
-sen=service_name \
-spn=span_name \
-dur=SPAN_TIME_IN_SECONDS
```

### Optional Parameters:
```
--dry-run=True|False
--debug=True|False
--time-shift=True|False
--parent-span-id=<16 character hex id>
--trace-id=<32 character hex id>
--span-id=<16 character hex id>
```

Use the final 3 optional parameters above when working with sub spans. See below for more information.

## Dry Run Mode
Add `--dr=True`, `--dry-run=True` or `--dry=True` to run without actually pushing any data.

## Debug Mode
Add `-x=True` or `--debug=True` for extra output

## Time Shifting
In "default mode" tracepusher starts a trace `now` and finishes it `SPAN_TIME_IN_SECONDS` in the future.

You may want to push timings for traces that have already occurred (eg. shell scripts). See https://github.com/agardnerIT/tracepusher/issues/4.

`--time-shift=True` means `start` and `end` times will be shifted back by whatever is specified as the `--duration`.

## Complex Tracing (Sub Span support)
![subspan schematic](assets/subspan.schematic.excalidraw.png)
![complex trace](assets/complex-trace.png)

> TLDR: Prefer to read code? See the [samples/script.sh](./samples/script.sh) for a working example.

tracepusher `v0.5.0` and above supports tracing any arbitrarily complex multi-span trace. It does so by allowing users to generate and pass in their own `trace-id` and `span-id`.

Consider the following batch script:

```
#!/bin/bash

main_time_start=0

counter=1
limit=5

while [ $counter -le $limit ]
do
  echo "in a loop. interation ${counter}" # 1, 2, 3, 4, 5
done

main_time_end=$SECONDS
duration=$(( main_time_end - main_time_start ))

```

As a trace, this would be represented as `1` parent span (that lasts for `5` seconds). "Inside" that parent span would be `5` sub spans, each denoting "once around the loop".

In the default mode, tracepusher will auto-generate trace and span IDs but you can generate your own and pass them in. For example:

```
# trace_id is 32 digits
# span_id is 16
trace_id=$(hexdump -vn16 -e'4/4 "%08X" 1 "\n"' /dev/urandom)
span_id=$(hexdump -vn8 -e'4/4 "%08X" 1 "\n"' /dev/urandom)
```
The parent span would look like the following. Notice the `--time-shift=True` parameter is set. If this **was not** set, the timings would not make sense.

### Parent Span Example
```
python3 tracepusher.py \
    --endpoint=http://localhost:4318 \
    --service-name="serviceA" \
    --span-name="main_span" \
    --duration=${duration} \
    --trace-id=${trace_id} \
    --span-id=${span_id} \
    --time-shift=True
```

### Sub Span Example
```
# Note: subspan time is tracked independently to "main" span time
while [ $counter -lt $limit ]
do
  # Calculate unique ID for this span
  sub_span_id=$(hexdump -vn8 -e'4/4 "%08X" 1 "\n"' /dev/urandom)
  sub_span_time_start=$SECONDS

  # Do real work here...
  sleep 1
  
  subspan_time_end=$SECONDS
  duration=$$(( $time_end - $time_start ))
  counter=$(( $counter + 1 ))

  python3 tracepusher.py \
    --endpoint=http://localhost:4318 \
    --service-name=serviceA \
    --span-name="subspan${counter}" \
    --duration=${duration} \
    --trace-id=${trace_id} \
    --parent-span-id=${span_id} \
    --span-id=${subspan_id} \
    --time-shift=True
done
```

## Spin up OpenTelemetry Collector

## Download Collector
The Python script will generate and push a trace to an OpenTelemetry collector. So of course, you need one available.

If you have a collector already available, go on ahead to run the tool. If you **don't** have one already available, follow these steps.

Download and extract the collector binary for your platform from [here](https://github.com/open-telemetry/opentelemetry-collector-releases/releases/tag/v0.71.0).

For example, for windows: `https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.71.0/otelcol-contrib_0.71.0_windows_amd64.tar.gz`

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

# Breaking Changes

## v0.3.0 to v0.4.0
Argument handling was entirely re-written for `v0.4.0` and `tracepusher` expects different arguments for [v0.3.0](https://github.com/agardnerIT/tracepusher/releases/tag/0.3.0) and [v0.4.0](https://github.com/agardnerIT/tracepusher/releases/tag/0.4.0).

[Here is the readme for v0.3.0](https://github.com/agardnerIT/tracepusher/tree/88e6479213a952eed7985d28b1ef49a4396fe992).

----------------------

# Contributing

All contributions are most welcome! Create an issue or a PR and see your name here!

<a href="https://github.com/agardnerit/tracepusher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=agardnerit/tracepusher" />
</a>

Made with [contrib.rocks](https://contrib.rocks).
