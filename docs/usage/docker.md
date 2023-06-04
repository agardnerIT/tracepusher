# Requirements and Prequisites
- A running OpenTelemetry collector (see below)
- Docker

## Basic Docker Usage

```
docker run gardnera/tracepusher:v0.6.0 \
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
```

For span atttribute types, see [Span Attribute Types](../reference/span-attribute-types.md).