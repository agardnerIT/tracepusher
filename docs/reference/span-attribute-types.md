## Span Attribute Types

The optional `-spnattrs` or equivalent long form version: `--span-attributes` exists to add span attributes to the spans that tracepusher creates.

Add as many attributes as you like.

### Formatting Span Attributes

Tracepusher will accept two possible inputs:

- `--span-attributes foo=bar`
- `--span-attributes foo=bar=<TYPE>`

In the first, the value is assumed to be of type `stringValue`.

In the second, **you** specify the value type. Possible types are: `stringValue`, `boolValue`, `intValue`, `doubleValue`, `arrayValue`, `kvlistValue` or `bytesValue`.

Separate each attribute with a space.

```
python tracepusher.py \
--endpoint http(s)://OTEL-COLLECTOR-ENDPOINT:4318
--service-name service_name \
--span-name spanA \
--duration 2 \
--span-attributes foo=bar foo2=23=intValue
```

```
docker run gardnera/tracepusher:v0.7.0 \
-ep http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
-sen service_name \
-spn span_name \
-dur SPAN_TIME_IN_SECONDS \
-spnattrs foo=bar foo2=bar2=stringValue
```

### Valid Types

The following are all valid:

- `stringValue`
- `boolValue`
- `intValue`
- `doubleValue`
- `arrayValue`
- `kvlistValue`
- `bytesValue`