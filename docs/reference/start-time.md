## Start Time

The optional flag `-st` or `--start-time` allows users to specify the span start time.

If not specified, tracepusher assumes a start time of `now`.

The two valid formats are:

1) A 19 digit string representing milliseconds since the epoch: eg. 1700967916494000000
2) "%Y-%m-%dT%H:%M:%S.%fZ" eg. "2023-11-26T03:05:16.844Z"

## Example 1: Unix timestamp

```
./tracepusher \
  --endpoint http://localhost:4318 \
  --span-name spanOne \
  --service-name serviceOne \
  --duration 2 \
  --duration-type s \
  --start-time 1700967916494000000
```

## Example 2: DateTime Format

```
./tracepusher \
  --endpoint http://localhost:4318 \
  --span-name spanOne \
  --service-name serviceOne \
  --duration 2 \
  --duration-type s \
  --start-time 2023-11-26T03:05:16.844Z
```