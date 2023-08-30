import kopf
from kubernetes import client
from datetime import datetime
import subprocess

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
collector_endpoint = ""

# Operator does not care
# When job is created
# Because start and stop time come on completion
# TODO Future: Create spans for job creation failures?

#@kopf.on.create('job')
#def on_create_job(spec, name, namespace, logger, **kwargs):
#    logger.info(f"{name} Job created...")

# Main logic
# This happens on every change event for a job
@kopf.on.event('job')
def on_event_job(event, spec, name, namespace, logger, **kwargs):

    # Be able to access globally defined collector_endpoint
    global collector_endpoint

    # optional
    # if job overrides global collector_endpoint
    # with an annotation
    # set as a new var
    collector_endpoint_to_use = ""

    # If job is annotated
    # with
    # annotations:
    #   tracepusher: "ignore"
    # Skip processing
    if "tracepusher/ignore" in event['object']['metadata']['annotations'] and event['object']['metadata']['annotations']['tracepusher/ignore'].lower() == "true":
        logger.info("Job is annotated. Will ignore.")
        return
    
    if "tracepusher/collector" in event['object']['metadata']['annotations']:
        logger.info("Job Annotated with a collector URL. This takes precedence over JobTracer. Use it.")
        collector_endpoint_to_use = event['object']['metadata']['annotations']['tracepusher/collector']
    else:
        collector_endpoint_to_use = collector_endpoint

    # If a collector endpoint
    # is not set
    # stop immediately
    # no point in continuing
    if collector_endpoint_to_use == "":
        logger.error("Collector endpoint is not set. Will not track this job.")
        return

    # Job finishes (successfully?) when all of the these conditions are true:
    # event.type == "MODIFIED"
    # event.status.startTime is not None
    # event.status.completionTime is not None
    if event['type'] == "MODIFIED" and event['object']['status'] is not None:

        # if event.object.status has either 'succeeded' or 'failed' fields
        # it has completed
        job_has_finished = False
        job_succeeded = None
        if "succeeded" in event['object']['status']:
            job_succeeded = True
            job_has_finished = True
        elif "failed" in event['object']['status']:
            job_succeeded = False
            job_has_finished = True
        
        # Job hasn't finished
        # Do not process further
        if not job_has_finished:
            return

        if job_has_finished:
            logger.info(f"{name}: JOB HAS FINISHED!")
        
        number_of_containers_in_job = len(event['object']['spec']['template']['spec']['containers'])

        # job start time is always present
        # regardless of job success or failure
        # set it now.
        # only job end time differs
        job_start_time_str = event['object']['status']['startTime']
        job_start_time = datetime.strptime(job_start_time_str, DATE_FORMAT)

        # If Job has a completionTime
        # It was successful
        # Otherwise it failed
        if job_succeeded:
            
            job_end_time_str = event['object']['status']['completionTime']
            job_end_time = datetime.strptime(job_end_time_str, DATE_FORMAT)

            logger.info(f"Job start time: {job_start_time} ({type(job_start_time)})")
            logger.info(f"Job end time: {job_end_time} ({type(job_end_time)})")
            
            duration_std = job_end_time - job_start_time
            duration = int((job_end_time - job_start_time).total_seconds())
            logger.info(f"{name}: Job duration (standard): {duration_std}")
            logger.info(f"{name}: Job duration: {duration}s")

            logger.info(f"Containers in Job: {number_of_containers_in_job}")

            logger.info(f"Collector endpoint: {collector_endpoint_to_use}")

            # Call tracepusher
            subprocess.call([
                "python3",
                "tracepusher.py",
                "-ep",
                collector_endpoint_to_use,
                "-sen",
                "k8s",
                "-spn",
                name,
                "-dur",
                f"{duration}",
                "--span-status",
                "OK",
                "--time-shift",
                "true",
                "-spnattrs",
                "type=job",
                f"namespace={namespace}",
                f"container_count={number_of_containers_in_job}"
                ])
        # Job failed
        if not job_succeeded:

            job_end_time_str = event['object']['status']['conditions'][0]['lastTransitionTime']
            job_end_time = datetime.strptime(job_end_time_str, DATE_FORMAT)

            logger.info(f"Failed end time str: {job_end_time_str}")
            logger.info(f"Failed end time: {job_end_time}")

            duration_std = job_end_time - job_start_time
            duration = int((job_end_time - job_start_time).total_seconds())
            logger.info(f"{name}: Job duration: {duration}s")

            # object.status.lastTransitionTime can be used for finish time
            # object.status.reason = "BackoffLimitExceeded"
            # object.status.message = "Job has reached..."
            # object.spec.backoffLimit
            failure_reason = event['object']['status']['conditions'][0]['reason']
            failure_message = event['object']['status']['conditions'][0]['message']
            backoff_limit = event['object']['spec']['backoffLimit']
            #logger.info(event['object']['spec'])

            # Call tracepusher
            tracepusher_cmd = [
                    "python3",
                    "tracepusher.py",
                    "-ep",
                    collector_endpoint_to_use,
                    "-sen",
                    "k8s",
                    "-spn",
                    name,
                    "-dur",
                    f"{duration}",
                    "--span-status",
                    "ERROR",
                    "--time-shift",
                    "true",
                    "-spnattrs",
                    "type=job",
                    f"namespace={namespace}",
                    f"container_count={number_of_containers_in_job}",
                    f"backoff_limit={backoff_limit}",
                    f"failure_message={failure_message}",
                    f"failure_reason={failure_reason}"
                ]
            
            # Read pod logs for job to get proper failure info
            api_instance = client.CoreV1Api()
            job_pods = api_instance.list_namespaced_pod(namespace=namespace, label_selector=f"job-name={name}")

            #print(f"GOT SOME PODS FOR JOB: {name}")
            for pod in job_pods.items:
                print(pod)

                # for each container in pod
                # get container name + error code
                for container_status in pod.status.container_statuses:
                    tracepusher_cmd.append(f"container-{container_status.name}-reason={container_status.state.terminated.reason}")
                    tracepusher_cmd.append(f"container-{container_status.name}-exitcode={container_status.state.terminated.exit_code}")
                    tracepusher_cmd.append(f"container-{container_status.name}-message={container_status.state.terminated.message}")
                
            # Call tracepusher
            subprocess.call(tracepusher_cmd)

# Happens once when a user
# Applies a kind: JobTracer CR
# Used for setup
@kopf.on.create('jobtracers')
def on_create_jobtracer(spec, name, namespace, logger, **kwargs):
    # This function updates the collector_endpoint global
    # prepare for this now...
    global collector_endpoint

    logger.info("Created a JobTracer...")
    namespace = namespace
    collector_endpoint = spec['collectorEndpoint']
    logger.info(f"Namespace is: {namespace}")
    logger.info(f"Spec is: {spec}")
    logger.info(f"Collector Endpoint is: {collector_endpoint}")

# Happens when a user re-applies
# a Kind: JobTracer yaml
# and thus forces an update
@kopf.on.update('jobtracers')
def on_update_jobtracer(spec, name, namespace, logger, **kwargs):
    # This function updates the collector_endpoint global
    # prepare for this now...
    global collector_endpoint

    logger.info("Updated a JobTracer...")
    namespace = namespace
    collector_endpoint = spec['collectorEndpoint']
    logger.info(f">> Collector Endpoint is: {collector_endpoint}")
