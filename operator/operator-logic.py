import kopf
from kubernetes import client
from datetime import datetime, timezone
import subprocess
import secrets

default_collector_endpoint = ""
jobs_to_process = []

def call_tracepusher(tracepusher_args):

    full_cmd = ['python3', 'tracepusher.py'] + tracepusher_args
    
    # Call tracepusher
    subprocess.call(full_cmd)

# type = "job" | "container"
def get_tz_aware_start_finish_times(object, type):

    DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    workload_succeeded = False
    start_time_str = ""
    finish_time_str = ""
    workload_start_time = None
    workload_end_time = None

    if type == "job":
        if "succeeded" in object['status']: workload_status = True

        start_time_str = object['status']['startTime']

        if workload_succeeded:
            finish_time_str = object['status']['completionTime']
        else:
            finish_time_str = object['status']['conditions'][0]['lastTransitionTime']

    if type == "container":
        start_time_str = object['state']['terminated']['startedAt']
        finish_time_str = object['state']['terminated']['finishedAt']

    # Do processing in case either field starts with a 
    # date of 1970
    # If start time is empty
    # set to be the same as the end time
    if start_time_str.startswith('1970'):
        start_time_str = finish_time_str
    
    # Make times timezone aware for UTC
    workload_start_time = datetime.strptime(start_time_str, DATE_FORMAT)
    workload_start_time = workload_start_time.replace(tzinfo=timezone.utc)
    workload_end_time = datetime.strptime(finish_time_str, DATE_FORMAT)
    workload_end_time = workload_end_time.replace(tzinfo=timezone.utc)

    duration_seconds = int((workload_end_time - workload_start_time).total_seconds())

    return workload_start_time, workload_end_time, duration_seconds


@kopf.on.event('pods')
def on_update_pod(event, spec, name, namespace, logger, **kwargs):
    global jobs_to_process

    # If this pod was spawned by a job, proceed
    if "job-name" in event['object']['metadata']['labels']:
        job_name = event['object']['metadata']['labels']['job-name']

        # Make composite key of job name + namespace
        # This is used to lookup the jobs the Operator SHOULD track
        job_key = f"{job_name}/{namespace}"

        # Skip jobs that should not be processed
        job_keys_to_track = [ item['key'] for item in jobs_to_process ]
        if job_key not in job_keys_to_track: return

        if event['object']['status']['phase'] == "Succeeded" or event['object']['status']['phase'] == "Failed":

            job_obj_from_tracker_list = next((item for item in jobs_to_process if item['key']==job_key), None)
            job_main_trace_id = job_obj_from_tracker_list['main_trace_id']
            job_main_span_id = job_obj_from_tracker_list['main_span_id']

            job_name = event['object']['metadata']['labels']['job-name']

            # Only send main trace when finalizers
            # are all done
            # (ie. no finalizers left in JSON)
            # In other words, skip if finalizers remain
            if "finalizers" in event['object']['metadata']:
                return

            container_statuses = event['object']['status']['containerStatuses']
            for container_status in container_statuses:

                container_span_status = "OK"

                container_name = container_status['name']
                container_exit_code = container_status['state']['terminated']['exitCode']
                container_message = ""
                # TODO: This is too presumptive
                # Let users annotate to give their own success code
                if container_exit_code != 0:
                    container_span_status = "Error"

                container_exit_reason = container_status['state']['terminated']['reason']
                container_start_time, container_end_time, container_duration = get_tz_aware_start_finish_times(container_status, "container")

                if "message" in container_status['state']['terminated']:
                    container_message = container_status['state']['terminated']['message']
                
                # Generate a unique span ID for this container
                # Link to main using trace_id and parent_span_id
                container_span_id = secrets.token_hex(8)

                # Call tracepusher
                tracepusher_args = [
                    "-ep",
                    job_obj_from_tracker_list['collector_endpoint'],
                    "-sen",
                    "k8s",
                    "-spn",
                    container_name,
                    "-dur",
                    f"{container_duration}",
                    "--span-status",
                    container_span_status,
                    "--time-shift",
                    "true",
                    "--trace-id",
                    job_main_trace_id,
                    "--parent-span-id",
                    job_main_span_id,
                    "-spnattrs",
                    "type=container",
                    f"namespace={namespace}",
                    f"exit_code={container_exit_code}",
                    f"reason={container_exit_reason}",
                    f"message={container_message}"
                ]
                call_tracepusher(tracepusher_args=tracepusher_args)


# This happens on every change event for a job
@kopf.on.event('job')
def on_event_job(event, spec, name, namespace, logger, **kwargs):

    # Be able to access globally defined default_collector_endpoint
    global default_collector_endpoint
    # Use this list to trace the jobs that SHOULD be processed
    global jobs_to_process

    # If job is annotated
    # with
    # annotations:
    #   tracepusher: "ignore"
    # Skip processing
    if "tracepusher/ignore" in event['object']['metadata']['annotations'] and event['object']['metadata']['annotations']['tracepusher/ignore'].lower() == "true":
        logger.info("Job is annotated. Will ignore.")
        return

    # optional
    # if job overrides global collector_endpoint
    # with an annotation
    # set as a new var
    collector_endpoint_to_use = default_collector_endpoint

    if "tracepusher/collector" in event['object']['metadata']['annotations']:
        collector_endpoint_to_use = event['object']['metadata']['annotations']['tracepusher/collector']

    # If a collector endpoint
    # is not set
    # stop immediately
    # no point in continuing
    if collector_endpoint_to_use == "":
        logger.info("Collector endpoint is not set. Will not track this job.")
        return
    
    # A valid job to track
    # If it isn't already in the list
    if event['type'] == "ADDED" or event['type'] == "MODIFIED":
        # Get existing keys and only add once
        # Create a composite key of job name + namespace
        # As there could be two identical job names in different namespaces
        job_name_key = f"{name}/{namespace}"
        keys = [ item['key'] for item in jobs_to_process ]
        if job_name_key not in keys:
            # Generate main trace ID and span ID
            # The trace_id will be common for all traces in this job
            main_trace_id = secrets.token_hex(16)
            main_span_id = secrets.token_hex(8)

            jobs_to_process.append({
                    "key": job_name_key,
                    "job_name": name,
                    "namespace": namespace,
                    "collector_endpoint": collector_endpoint_to_use,
                    "main_trace_id": main_trace_id,
                    "main_span_id": main_span_id
            })

    # Job finishes when all of the these conditions are true:
    if event['type'] == "MODIFIED" and event['object']['status'] is not None:

        # if event.object.status has either 'succeeded' or 'failed' fields
        # it has completed
        job_status = None
        job_has_finished = False
        job_reason = ""
        job_message = ""
        if "succeeded" in event['object']['status']:
            job_status = "OK"
            job_has_finished = True
        elif "failed" in event['object']['status']:
            job_status = "ERROR"
            job_has_finished = True
            job_reason = event['object']['status']['conditions'][0]['reason']
            job_message = event['object']['status']['conditions'][0]['message']
        
        # Job hasn't finished
        # Do not process further
        if not job_has_finished:
            return

        logger.info(f"Job has finished")

        job_obj_from_tracker_list = next((item for item in jobs_to_process if item['key']==job_name_key), None)
        job_main_trace_id = job_obj_from_tracker_list['main_trace_id']
        job_main_span_id = job_obj_from_tracker_list['main_span_id']
        job_collector_url = job_obj_from_tracker_list['collector_endpoint']

        #logger.info(f"List before removal: {jobs_to_process}")
        if job_obj_from_tracker_list is not None:
            jobs_to_process.remove(job_obj_from_tracker_list)
        #logger.info(f"List after removal: {jobs_to_process}")

        job_start_time, job_end_time, job_duration = get_tz_aware_start_finish_times(event['object'], "job")
        logger.info(f"JOB Details. JST: {job_start_time} - JET: {job_end_time} - JD: {job_duration}")

        # Call tracepusher
        tracepusher_args = [
                "-ep",
                job_obj_from_tracker_list['collector_endpoint'],
                "-sen",
                "k8s",
                "-spn",
                name,
                "-dur",
                f"{job_duration}",
                "--span-status",
                job_status,
                "--time-shift",
                "true",
                "--trace-id",
                job_main_trace_id,
                "--span-id",
                job_main_span_id,
                "-spnattrs",
                "type=job",
                f"namespace={namespace}",
                f"job_message={job_message}",
                f"job_reason={job_reason}"
            ]
        call_tracepusher(tracepusher_args=tracepusher_args)


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
