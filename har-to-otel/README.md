# Chrome DevTools HAR file to OpenTelemetry converter

> Alpha release! Use with caution

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

## Notes

1) This is temporary documentation during development. Documentation will eventually move to the [tracepusher website](https://agardnerit.github.io/tracepusher)
2) The `tracepusher.py` file in this directory is (currently) slightly different (has some new features) compared with the "main" [tracepusher.py](../tracepusher.py)
3) No test harness exists for this tool yet. Get involved and help by contributing it!