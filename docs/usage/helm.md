# Trace Helm with Tracepusher

It is possible to trace `helm` commands using tracepusher.

Just add the word `trace` to any regulard `helm` command.

For example, `helm version` becomes `helm trace version`

## Instructions

1. Download and add a tracepusher binary to your `PATH`
1. Install `helm trace` plugin:

```
helm plugin install https://github.com/agardnerit/helm-trace
```

Full documentation is available on the [helm trace GitHub repo](https://github.com/agardnerIT/helm-trace).