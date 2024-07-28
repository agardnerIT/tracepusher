# Download binary

Download the relevant binary from the [GitHub releases page](https://github.com/agardnerit/tracepusher/releases/latest).

## Run tracepusher

```
./tracepusher \
  -ep http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
  --insecure false \
  -sen service_name \
  -spn span_name \
  -dur SPAN_TIME_IN_SECONDS
```

### Optional Parameters

```
--dry-run True|False
--debug True|False
--time-shift True|False
--duration-type ms|s (defaults to `s` > seconds)
--parent-span-id <16 character hex id>
--trace-id <32 character hex id>
--span-id <16 character hex id>
--span-attributes key=value key2=value2=type
--span-events timeOffsetInMillis=EventName=AttributeKey=AttributeValue=type [event2...] [event3...]
--span-kind UNSPECIFIED|INTERNAL|CLIENT|SERVER|CONSUMER|PRODUCER (defaults to `INTERNAL`)
--span-status OK|ERROR (defaults to OK)
```

For span atttribute types, see [Span Attribute Types](../reference/span-attribute-types.md).

For span events, see [Span events](../reference/span-events.md)

For multi-span traces, see [multi span traces](../reference/multi-span-traces.md)

For duration type, see [duration type](../reference/duration-type.md)

For span kind, see [span kind](../reference/span-kind.md)
