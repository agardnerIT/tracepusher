## Span Status

The optional flag `-ss` or `--span-status` allows users to specify the span status.

If not specified, tracepusher assumes an `OK` status.

For reference, these map to values of `0` (Unset), `1` (OK) or `2` (Error) according to the [OpenTelemetry specification](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/trace/v1/trace.proto#L270-#L278).

### Valid Span Statuses

These are case insensitive:

- `OK` (default)
- `ERROR`
- `UNSET` (if you use anything other than "OK" or "ERROR")

### Examples

#### Defaults to OK

```shell
./tracepusher \
  -ep http://localhost:4318 \
  -sen serviceA \
  -spn span1 \
  -dur 2
```

#### Explicitly set to OK

```shell
./tracepusher \
  -ep http://localhost:4318 \
  -sen serviceA \
  -spn span1 \
  -dur 2 \
  --span-status OK
```

#### Explicitly set to Error
```shell
./tracepusher \
  -ep http://localhost:4318 \
  -sen serviceA \
  -spn span1 \
  -dur 2 \
  --span-status ERROR
```

#### Invalid value (defaults to Unset)

```shell
./tracepusher \
  -ep http://localhost:4318 \
  -sen serviceA \
  -spn span1 \
  -dur 2 \
  --span-status ABC123
```