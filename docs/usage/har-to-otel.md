# Chrome DevTools HAR File to OpenTelemetry Converter

This tool converts a `.har` file to OpenTelemetry traces and sends them to an OpenTelemetry collector using tracepusher.

## Feedback Required!

If you use this, please provide feedback (good or bad) on [this issue](https://github.com/agardnerIT/tracepusher/issues/72).

When the tool is confirmed as stable, standalone binaries will be built.

## Usage

```
docker run \
  --mount type=bind,source="$(pwd)",target=/files \
  gardnera/har-to-otel:dev \
  -f /files/YOUR-HAR-FILE.har \
  -ep http://host.docker.internal:4318 \
  --insecure true
```

### Optional flags

If set, these are added as span attributes:

- `--timings [true|false]` (defaults to `true`)
- `--request-headers [true|false]` (defaults to `false`)
- `--response-headers [true|false]` (defaults to `false`)
- `--request-cookies [true|false]` (defaults to `false`)
- `--response-cookies [true|false]` (defaults to `false`)
- `--debug [true|false]` (defaults to `false`)
- `--dry-run [true|false]` (defaults to `false`)