# OpenTelemetry TracePusher

## [View the tracepusher docs](https://agardnerit.github.io/tracepusher)

Generate and push OpenTelemetry Trace data to an endpoint in JSON format.

![architecture](assets/architecture.png)
![trace](assets/trace.png)

# Uses

- [Trace CICD Pipelines with OpenTelemetry](samples/gitlab/README.md)
- [Trace shell scripts with OpenTelemetry](samples/script.sh)
- Trace anything with OpenTelemetry!

# Try In Browser
- [tracepusher with open source software (Jaeger)](https://killercoda.com/agardnerit/scenario/tracepusherOSS)
- [tracepusher with Dynatrace](https://killercoda.com/agardnerit/scenario/tracepusherDT)

# Requirements and Prequisites
- A running OpenTelemetry collector (see below)
- Requires `requests` module (`pip install -r requirements.txt`)
- Requires Python 3 or docker.

## Python3 Usage

`python3 tracepusher.py -h` or `python3 tracepusher.py --help` shows help text.

```
python tracepusher.py \
--endpoint http(s)://OTEL-COLLECTOR-ENDPOINT:4318
--service-name service_name \
--span-name spanA \
--duration 2
```

## Docker Usage

```
docker run gardnera/tracepusher:v0.6.0 \
-ep http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
-sen service_name \
-spn span_name \
-dur SPAN_TIME_IN_SECONDS
```

### Optional Parameters:
```
--dry-run True|False
--debug True|False
--time-shift True|False
--parent-span-id <16 character hex id>
--trace-id <32 character hex id>
--span-id <16 character hex id>
--span-attributes key=value [key2=value2...]
```

Use `parent-span-id` `trace-id` and `span-id` optional parameters when working with sub spans. See below for more information.

Use `span-attributes` to add `key=value` pairs of [span attributes](https://opentelemetry.io/docs/instrumentation/python/manual/#add-attributes-to-a-span) to your span. See below for more information.

## Dry Run Mode
Add `--dr True`, `--dry-run True` or `--dry True` to run without actually pushing any data.

## Debug Mode
Add `-x True` or `--debug True` for extra output

## Time Shifting
In "default mode" tracepusher starts a trace `now` and finishes it `SPAN_TIME_IN_SECONDS` in the future.

You may want to push timings for traces that have already occurred (eg. shell scripts). See https://github.com/agardnerIT/tracepusher/issues/4.

`--time-shift True` means `start` and `end` times will be shifted back by whatever is specified as the `--duration`.

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
    --endpoint http://localhost:4318 \
    --service-name "serviceA" \
    --span-name "main_span" \
    --duration ${duration} \
    --trace-id ${trace_id} \
    --span-id ${span_id} \
    --time-shift True
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
    --endpoint http://localhost:4318 \
    --service-name serviceA \
    --span-name "subspan${counter}" \
    --duration ${duration} \
    --trace-id ${trace_id} \
    --parent-span-id ${span_id} \
    --span-id ${subspan_id} \
    --time-shift True
done
```

## Span Attributes

> Only supported with `v0.6.0` and above.

See [span attribute types](https://agardnerit.github.io/tracepusher/reference/span-attribute-types/)

## Spin up OpenTelemetry Collector

See [OpenTelemetry Collector configuration](https://agardnerit.github.io/tracepusher/reference/otel-col)

# Adopters

Do you use tracepusher? Thanks and we'd love to know!

Submit a PR and add your details to [ADOPTERS.md](ADOPTERS.md)

# FAQs

See [FAQ](https://agardnerit.github.io/tracepusher/faq).

# Breaking Changes

See [Breaking changes](https://agardnerit.github.io/tracepusher/breaking-changes)

# Building

Run all build commands from the root directory:

```
docker buildx build --platform linux/arm64,linux/amd64 --push -t tracepusher:dev-ci -f ./docker/ci/Dockerfile .
docker buildx build --platform linux/arm64,linux/amd64 --push -t tracepusher:dev -f ./docker/standard/Dockerfile .
```

----------------------

# Contributing

All contributions are most welcome!

Get involved:
- Tackle a [good first issue](https://github.com/agardnerIT/tracepusher/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22)
- Create an issue to suggest something new
- File a PR to fix something

<a href="https://github.com/agardnerit/tracepusher/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=agardnerit/tracepusher" />
</a>

Made with [contrib.rocks](https://contrib.rocks).
