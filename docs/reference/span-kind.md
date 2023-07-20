## Span Kind

The optional flag `-sk` or `--span-kind` allows users to specify the span kind.

If not specified, tracepusher generates `INTERNAL` type spans. But using the above parameter, a user can override this.

### Valid Span Types

- `UNSPECIFIED` (tracepusher automatically transforms this to `INTERNAL` as per the spec)
- `INTERNAL` (default)
- `CLIENT`
- `SERVER`
- `CONSUMER`
- `PRODUCER`

### Example

```shell
./tracepusher \
  -ep http://localhost:4318 \
  -sen serviceA \
  -spn span1 \
  -dur 2 \
  --span-kind CONSUMER
```