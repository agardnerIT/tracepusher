## Span Events

The optional `-spnevnts` or equivalent long form version: `--span-events` exists to add span events to the spans that tracepusher creates.

Add as many events as you like.

### Formatting Span Events

Span events are formatted as follows. The first 4 parameters are mandatory. The fifth is optional.

```
<eventTimeOffsetInMillisFromSpanStartTime>=<eventName>=<eventKey>=<eventValue>
```

In the first, the value is assumed to be of type `stringValue`.

or

```
<eventTimeOffsetInMillisFromSpanStartTime>=<eventName>=<eventKey>=<eventValue>=<eventValueType>
```

For example, to push an event that should be denoted at 100 milliseconds _after_ the span start time, where the event name is `eventA`, the key is `feature_flag.key`, the value is `hexColor` and the event value type (implied) is `stringValue`:

```
python ~/tracepusher/tracepusher.py \
  --endpoint http://localhost:4318 \
  --service-name serviceA \
  --span-name span1 \
  --duration 2 \
  --span-events 0=eventA=feature_flag.key=hexColor
```

To send an event that should be attached at the beginning of the span, with a key of `userID` and a type set as an integer:

```
python ~/tracepusher/tracepusher.py \
  --endpoint http://localhost:4318 \
  --service-name serviceA \
  --span-name span1 \
  --duration 2 \
  --span-events 0=eventA=userID=23=intValue
```

Multiple
Tracepusher will accept two possible inputs:

- `--span-attributes 0=eventName=key=vaue`
- `--span-attributes 0=eventName=key=value=<TYPE>`

## Send Multiple Span Events

Separate each attribute with a space.

```
python tracepusher.py \
--endpoint http(s)://OTEL-COLLECTOR-ENDPOINT:4318
--service-name service_name \
--span-name spanA \
--duration 2 \
--span-events 0=eventA=foo=bar 0=eventA=userID=23=intValue
```

```
docker run gardnera/tracepusher:v0.8.0 \
-ep http(s)://OTEL-COLLECTOR-ENDPOINT:4318 \
-sen service_name \
-spn span_name \
-dur SPAN_TIME_IN_SECONDS \
-spnevnts 0=eventA=foo=bar 0=eventA=userID=23=intValue
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
