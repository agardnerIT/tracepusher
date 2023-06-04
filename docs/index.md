# OpenTelemetry tracepusher

Trace anything with OpenTelemetry!

Generate and push OpenTelemetry Trace data to an endpoint in JSON format.

![architecture](assets/architecture.png)
![trace](assets/trace.png)
![complex trace](assets/complex-trace.png)

## Watch: Tracepusher in Action

<iframe width="560" height="315" src="https://www.youtube.com/embed/zZDFQNHepyI" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

##  Uses

- [Trace CICD Pipelines with OpenTelemetry](https://github.com/agardnerIT/tracepusher/blob/main/samples/gitlab/README.md)
- [Trace shell scripts with OpenTelemetry](https://github.com/agardnerIT/tracepusher/blob/main/samples/script.sh)
- [Use tracepusher in a CICD system](usage/ci.md)
- Trace anything with OpenTelemetry

## Try tracepusher
See [try tracepusher](try.md)

## Quick Start

```
docker run gardnera/tracepusher:v0.6.0 \
--endpoint http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
--service-name service_name \
--span-name span_name \
--duration SPAN_TIME_IN_SECONDS
```

## Advanced Usage

See the following pages for advanced usage and reference information for the flags:

- [Docker usage](usage/docker.md)
- [Python usage](usage/python.md)
- [CI system usage](usage/ci.md)
- [Complex (Multi Span) Traces](reference/multi-span-traces.md)
- [Span time shifting](reference/time-shifting.md)
- [Span attributes and span attribute types](reference/span-attribute-types.md)
- [tracepusher flag reference pages](reference/index.md)
