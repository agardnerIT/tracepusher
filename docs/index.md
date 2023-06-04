# OpenTelemetry tracepusher

Generate and push OpenTelemetry Trace data to an endpoint in JSON format.

![architecture](assets/architecture.png)
![trace](assets/trace.png)
![complex trace](assets/complex-trace.png)

##  Uses

- [Trace CICD Pipelines with OpenTelemetry](samples/gitlab/README.md)
- [Trace shell scripts with OpenTelemetry](samples/script.sh)
- Trace anything with OpenTelemetry!

## Try tracepusher
See [try tracepusher](try.md)

## Quick Start

```
docker run gardnera/tracepusher:v0.6.0 \
-ep http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
-sen service_name \
-spn span_name \
-dur SPAN_TIME_IN_SECONDS
```

