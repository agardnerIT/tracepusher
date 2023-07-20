## Span Duration and Duration Type

The optional flag `-dt` or `--duration-type` allows users to specify the span duration type.

If not specified, tracepusher generates spans of a duration type in `seconds`. Using the above parameter, a user can override this.

### Valid Span Duration Types

- `s`: seconds (default)
- `ms`

### Examples

Generate a 2 second long span:

```shell
./tracepusher \
  -ep http://localhost:4318 \
  -sen serviceA \
  -spn span1 \
  -dur 2
```

equivalent to:

```shell
./tracepusher \
  -ep http://localhost:4318 \
  -sen serviceA \
  -spn span1 \
  -dur 2 \
  --duration-type s
```

Generate a span of `1234` milliseconds:

```shell
./tracepusher \
  -ep http://localhost:4318 \
  -sen serviceA \
  -spn span1 \
  -dur 1234 \
  --duration-type ms
```