# Requirements and Prequisites
- A running OpenTelemetry collector
- Docker

## Basic Docker Usage

```
docker run gardnera/tracepusher:v0.7.0 \
-ep http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
-sen service_name \
-spn span_name \
-dur SPAN_TIME_IN_SECONDS
```

### Optional Parameters

```
--dry-run True|False
--debug True|False
--time-shift True|False
--parent-span-id <16 character hex id>
--trace-id <32 character hex id>
--span-id <16 character hex id>
--span-attributes key=value key2=value2=type
--span-events timeOffsetInMillis=EventName=AttributeKey=AttributeValue=type [event2...] [event3...]
```

For span atttribute types, see [Span Attribute Types](../reference/span-attribute-types.md).

For span events, see [Span events](../reference/span-events.md)

For multi-span traces, see [multi span traces](../reference/multi-span-traces.md)