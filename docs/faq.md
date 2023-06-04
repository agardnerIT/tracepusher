## Why Does This Exist?
Why, when [tracegen](https://www.jaegertracing.io/docs/1.42/tools/) and the replacement [telemetrygen](https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/9597) exist, does this exist?

This tool does not replace or supercede those tools in any way. For lots of usecases and people, those tools will be better.

However, they hide the inner-workings (the *how*). For someone getting started or wanting to truly understand what is happening, there is "too much magic". Stuff "just works" whereas tracepusher is more explicit - and thus (I believe) easier to see how the pieces fit together.

The trace data that tracepusher generates is also customisable whereas "you get what you get" with `tracegen / telemetrygen`.