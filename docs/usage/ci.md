## tracepusher CI-ready image

> ℹ️ v0.8.0 and above have standalone, platform-specific binaries which are probably easier to use and better suited to this usecase.
>
> We suggest trying the standalone binary (attached to every GitHub release) first - before using this docker image.
>
> We would love your feedback as we consider retiring this `-ci` image in future.

The `gardnera/tracepusher:v0.8.0-ci` image is CI ready.

This containers drops you into a normal shell where you have access to various tools like openssl (for generating UUIDs).

Tracepusher can be executed using Python from within this container. See [Python usage instructions](python.md) for more info.

### Example: Tracing GitLab pipelines

See [Tracing GitLab pipelines with tracepusher on YouTube](https://youtu.be/zZDFQNHepyI) for a walkthrough and get started with [the sample script](../../samples/gitlab/README.md).
