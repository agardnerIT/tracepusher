## Time Shifting

In "default mode" tracepusher starts a trace `now` and finishes it `SPAN_TIME_IN_SECONDS` in the future.

You may want to push timings for traces that have already occurred (eg. shell scripts). See https://github.com/agardnerIT/tracepusher/issues/4.

`--time-shift true` means `start` and `end` times will be shifted back by whatever is specified as the `--duration`.
