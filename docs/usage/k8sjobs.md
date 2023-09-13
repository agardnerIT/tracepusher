## Trace Kubernetes Jobs and CronJobs with tracepusher

Install the tracepusher job operator to automatically generate OpenTelemetry traces for any `Job` and `CronJobs` on the cluster.

### Prerequisites

First, make sure you have an OpenTelemetry collector running somewhere.

### 1. Install Custom Resource Definitions

Install the tracepusher CRDs:

```shell
kubectl apply -f https://raw.githubusercontent.com/agardnerIT/tracepusher/main/operator/crds.yml
```

### 2. Create One (or more) JobTracer Objects

A `JobTracer` should be created, one per namespace.

This defines the defaults for that namespace.

You can override the details on a per job basis.

For example, to trace all `Jobs` in the default namespace, download this file, modify the collector endpoint to point to your collector 

```shell
wget https://raw.githubusercontent.com/agardnerIT/tracepusher/main/samples/jobtraceroperator/jobtracer.yml
# Modify spec.collectorEndpoint
kubectl apply -f jobtracer.yaml
```

### 3. Create a Job or CronJob

Now create a `Job` or `CronJob` as normal:

```
cat <<EOF | kubectl create -f -
---
apiVersion: batch/v1
kind: Job
metadata:
  name: pi
  namespace: default
  #annotations:
  #  tracepusher/ignore: "true"
  #  tracepusher/collector: "http://example.com:4318"
spec:
  template:
    spec:
      containers:
      - name: pi
        image: perl:5.34.0
        command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
      restartPolicy: Never
  backoffLimit: 0
EOF
```

Note the optional annotations. If set, these override the `JobTracer` settings.