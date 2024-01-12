# Chrome DevTools HAR File to OpenTelemetry Converter

![tracepusher HAR to OpenTelemetry Converter](assets/har-to-otel.jpg)

This tool converts a `.har` file to OpenTelemetry traces and sends them to an OpenTelemetry collector using tracepusher.

## Usage

```
docker run \
  --mount type=bind,source="$(pwd)",target=/files \
  gardnera/har-to-otel:0.10.0 \
  -f /files/YOUR-HAR-FILE.har \
  -ep http://host.docker.internal:4318 \
  --insecure true
```

(standalone binaries coming soon...)

### Optional flags

If set, these are added as span attributes:

- `--timings [true|false]` (defaults to `true`)
- `--request-headers [true|false]` (defaults to `false`)
- `--response-headers [true|false]` (defaults to `false`)
- `--request-cookies [true|false]` (defaults to `false`)
- `--response-cookies [true|false]` (defaults to `false`)
- `--debug [true|false]` (defaults to `false`)
- `--dry-run [true|false]` (defaults to `false`)