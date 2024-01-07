# OpenTelemetry tracepusher

Trace anything with OpenTelemetry!

Generate and push OpenTelemetry Trace data to an endpoint in JSON format.

![architecture](assets/architecture.png)
![complex trace](assets/complex-trace.png)

## Watch: Tracepusher in Action

<iframe width="560" height="315" src="https://www.youtube.com/embed/zZDFQNHepyI" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

Want to do a similar thing with logs? Check out [logpusher](https://agardnerit.github.io/logpusher).

##  Uses

- [Trace Kubernetes Jobs and CronJobs with OpenTelemetry](usage/k8sjobs.md)
- [Trace CICD Pipelines with OpenTelemetry](https://github.com/agardnerIT/tracepusher/blob/main/samples/gitlab/README.md)
- [Trace shell scripts with OpenTelemetry](https://github.com/agardnerIT/tracepusher/blob/main/samples/script.sh)
- [Trace Helm with tracepusher](usage/helm.md)
- [Use tracepusher in a CICD system](usage/ci.md)
- Trace anything with OpenTelemetry

## Try tracepusher
See [try tracepusher](try.md)

## Quick Start

Tracepusher is available as:

- [Standalone binaries](usage/standalone.md)
- [Python script](usage/python.md)
- [Docker image](usage/docker.md)
- [Kubernetes Operator](usage/k8sjobs.md)

Download the binary [from the releases page](https://github.com/agardnerIT/tracepusher/releases/latest) then run:

```
./tracepusher --endpoint http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
--service-name service_name \
--span-name span_name \
--duration SPAN_TIME_IN_SECONDS
```

## Advanced Usage

See the following pages for advanced usage and reference information for the flags:

- [Standalone binary usage](usage/standalone.md)
- [Docker usage](usage/docker.md)
- [Python usage](usage/python.md)
- [CI system usage](usage/ci.md)
- [Complex (Multi Span) Traces](reference/multi-span-traces.md)
- [Span time shifting](reference/time-shifting.md)
- [Span attributes and span attribute types](reference/span-attribute-types.md)
- [Span events](reference/span-events.md)
- [Span status](reference/span-status.md)
- [Insecure flag](reference/insecure-flag.md)
- [Start time flag](reference/start-time.md)
- [tracepusher flag reference pages](reference/index.md)
