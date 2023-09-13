import kopf
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from datetime import datetime, timezone
import subprocess
import secrets

# Job names are listed in here while they're being traced
jobs_to_process = []

# Cache built from JobTracer objects
# Which tracks which namespaces to trace
namespaces_to_trace = [] 

# Initialise the Operator
# The operator is starting
# Read each JobTracer in the cluster
# Populate the namespaces_to_trace list
@kopf.on.startup()
def initialise_operator(logger, **kwargs):

    logger.info("#"*30)

    try:
        configuration = config.load_incluster_config()   
    except Exception:
        logger.info("Cannot load config from within cluster. Loading local config. This is OK if you are a developer and running locally.")
        configuation = config.load_config()

    with client.ApiClient() as api_client:
        api_instance = client.CustomObjectsApi(api_client)
        try: 
            api_response = api_instance.list_cluster_custom_object(
                group="tracers.tracepusher.github.io",
                version="v1",
                plural="jobtracers",
                pretty=True,
                timeout_seconds=10
                )
            
            for jt in api_response.get('items'):

                namespaces_to_trace.append({
                    "namespace": jt['metadata']['namespace'],
                    "spec": jt['spec']
                })

                logger.info(f"Print List: {namespaces_to_trace}")
                logger.info('#'*30)
        except ApiException as e:
            logger.info("Exception when calling CustomObjectsApi->list_cluster_custom_object: %s\n" % e)

def get_jobs_to_track_keys():
    return [ item['key'] for item in jobs_to_process ]

def get_namespace_object(namespace):
    return next((item for item in namespaces_to_trace if item['namespace']==namespace), None)

# Given a job_key in the form "jobName/Namespace"
# Returns the job object to process
# or None
def get_job_to_process_object(job_key):
    if "/" not in job_key:
        logger.error(f"Invalid job_key syntax for: {job_key}. Must be 'jobName/Namespace'. Investigate!")
        return None
    return next((item for item in jobs_to_process if item['key']==job_key), None)

def add_job_to_toprocess_list(name, namespace, collector_endpoint, logger):
    # Generate main trace ID and span ID
    # The trace_id will be common for all traces in this job
    job_name_key = f"{name}/{namespace}"
    main_trace_id = secrets.token_hex(16)
    main_span_id = secrets.token_hex(8)

    jobs_to_process.append({
        "key": job_name_key,
        "job_name": name,
        "namespace": namespace,
        "collector_endpoint": collector_endpoint,
        "main_trace_id": main_trace_id,
        "main_span_id": main_span_id
    })
    logger.info(f"Added new job: {job_name_key} to list. List is now: {jobs_to_process}")

def update_job(name, namespace, collector_endpoint, logger):
    job_name_key = f"{name}/{namespace}"
    job_to_process = get_job_to_process_object(job_key=job_name_key)
    if job_to_process is not None:
        job_to_process['collector_endpoint'] = collector_endpoint
    
    logger.info(f"Updated Job: {job_name_key}. List is now: {jobs_to_process}")

def delete_job(name, namespace):
    job_name_key = f"{name}/{namespace}"
    job_to_delete = get_job_to_process_object(job_key=job_name_key)
    if job_to_delete is not None:
        jobs_to_process.remove(job_to_delete)

def call_tracepusher(tracepusher_args, logger):

    full_cmd = ['python3', 'tracepusher.py'] + tracepusher_args

    logger.info(f"TP ARGS: {tracepusher_args}")
    
    # Call tracepusher
    subprocess.call(full_cmd)

# Kopf Filter
# Custom filter to only react to new events
# Ignoring those which happened prior to operator
# Startup
def is_new_event(event, **_):
    if event['type'] is None: return False
    else: return True

# Kopf filter
# Return true if Pod was spawned by a job
# ie. has a "job-name" label
def is_pod_spawned_by_job(event, **_):
    if event['object']['kind'] == "Pod" and "job-name" in event['object']['metadata']['labels']: return True
    return False

# Kopf filter
# Only process events without finalizers
def has_no_finalizers(event, **_):
    if "finalizers" in event['object']['metadata']: return False
    return True

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


@kopf.on.event(
    'pods',
    annotations={"tracepusher/ignore": kopf.ABSENT},
    when=kopf.all_([is_new_event, is_pod_spawned_by_job, has_no_finalizers]))
def on_update_pod(event, spec, name, namespace, logger, **kwargs):

    # If pod is being deleted, ignore
    # Do not send a trace for a pod deletion
    if event["type"] == "DELETED": return

    job_name = event['object']['metadata']['labels']['job-name']

    # Make composite key of job name + namespace
    # This is used to lookup the jobs the Operator SHOULD track
    job_key = f"{job_name}/{namespace}"

    # Skip jobs that should not be processed
    job_keys_to_track = get_jobs_to_track_keys()
    logger.info(f"Job Keys: {job_keys_to_track}")
    if job_key not in job_keys_to_track: return

    if event['object']['status']['phase'] == "Succeeded" or event['object']['status']['phase'] == "Failed":

        job_obj_from_tracker_list = get_job_to_process_object(job_key)
        if job_obj_from_tracker_list is None:
            logger.error(f"No job in jobs_to_process list for job_key {job_key}. Error. Investigate!")
            return
        job_main_trace_id = job_obj_from_tracker_list['main_trace_id']
        job_main_span_id = job_obj_from_tracker_list['main_span_id']

        job_name = event['object']['metadata']['labels']['job-name']

        container_statuses = event['object']['status']['containerStatuses']
        for container_status in container_statuses:

            container_span_status = "OK"

            container_name = container_status['name']
            container_exit_code = container_status['state']['terminated']['exitCode']
            container_message = ""
            # TODO: This is too presumptive
            # Let users annotate to give their own success code
            if container_exit_code != 0: container_span_status = "Error"

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
            call_tracepusher(tracepusher_args=tracepusher_args, logger=logger)

# This happens on every change event for jobs
# That are NOT annotated with "tracepusher/ignore"
@kopf.on.event(
    'job',
    annotations={"tracepusher/ignore": kopf.ABSENT},
    when=is_new_event)
def on_event_job(event, spec, name, namespace, logger, **kwargs):

    tracker_details = get_namespace_object(namespace)
    if tracker_details is None:
        # Have not been asked to trace this namespace
        # Return quickly and do not process further
        logger.info(f"Did not find tracker_details in list. We are not configured to track: {namespace}")
        logger.info(f"tracker list is: {namespaces_to_trace}")
        return
    
    # If job is deleted
    # Remove from list
    # Note: jobs are deleted elsewhere during normal operation
    # This logic catches a side-issue
    # Where a job exists, the operator restarts and THEN
    # the job is deleted
    if event['type'] == "DELETED":
        logger.info(f">> DELETED A JOB: {name}/{namespace}")
        delete_job(name, namespace)
        # Do not re-trace a deleted job
        return

    # Get the collector endpoint
    namespace_default_collector_endpoint = tracker_details['spec']['collectorEndpoint']
    collector_endpoint_to_set = namespace_default_collector_endpoint
    logger.info(f"Got collector endpoint for the namespace from tracker_details: {namespace_default_collector_endpoint}")

    # Check for an annotation on the Job which overrides JobTracer global
    # collector endpoint
    if "tracepusher/collector" in event['object']['metadata']['annotations']:
        collector_endpoint_to_set = event['object']['metadata']['annotations']['tracepusher/collector']
        logger.info(f"Got a collector endpoint Override for job: {name} in namespace: {namespace}. Overridden collector URL is: {collector_endpoint_to_set}")

    # If a collector endpoint
    # is not set
    # stop immediately
    # no point in continuing
    if collector_endpoint_to_set == "":
        logger.info("Collector endpoint is not set. Will not track this job.")
        return
    else:
        # Get existing keys and only add once
        # Create a composite key of job name + namespace
        # As there could be two identical job names in different namespaces
        job_name_key = f"{name}/{namespace}"

        logger.info(f"Tracking job: {name} (job_name_key is {job_name_key}) with collector endpoint: {collector_endpoint_to_set}")
        # Update the collector URL on the global list now
        job_to_update = get_job_to_process_object(job_key=job_name_key)
        # If this is None, the Job existed before the operator started
        # So the list could be empty. Add it now
        if job_to_update is None:
            logger.info("Adding job: {name} to WILL PROCESS list.")
            add_job_to_toprocess_list(name=name,namespace=namespace,collector_endpoint=collector_endpoint_to_set, logger=logger)
        else:
            update_job(name=name, namespace=namespace, collector_endpoint=collector_endpoint_to_set, logger=logger)
            logger.info(f"Need to update {name}/{namespace} with new collector URL: {collector_endpoint_to_set}")

        logger.info(f"Printing new list: {jobs_to_process}")
    
    # A valid job to track
    # If it isn't already in the list
    if event['type'] == "ADDED" or event['type'] == "MODIFIED":
        # Get existing keys and only add once
        # Create a composite key of job name + namespace
        # As there could be two identical job names in different namespaces
        job_name_key = f"{name}/{namespace}"
        keys = [ item['key'] for item in jobs_to_process ]
        if job_name_key not in keys:
            add_job_to_toprocess_list(name, namespace, collector_endpoint_to_set)
        else: # job is already in the list, alter it
            job_to_update = get_job_to_process_object(job_key=job_name_key)
            logger.info(f"Need to update {job_to_update['key']} with new collector URL: {collector_endpoint_to_set}")
            job_to_update['collector_endpoint'] = collector_endpoint_to_set
            logger.info(f"Printing new list: {jobs_to_process}")

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

        job_obj_from_tracker_list = get_job_to_process_object(job_key=job_name_key)

        job_main_trace_id = job_obj_from_tracker_list['main_trace_id']
        job_main_span_id = job_obj_from_tracker_list['main_span_id']
        job_collector_url = job_obj_from_tracker_list['collector_endpoint']

        #logger.info(f"List before removal: {jobs_to_process}")
        if job_obj_from_tracker_list is not None:
            delete_job(name=name,namespace=namespace)
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
        call_tracepusher(tracepusher_args=tracepusher_args, logger=logger)


# Whenever a JobTracer object
# is created or updated
@kopf.on.create('jobtracers')
@kopf.on.update('jobtracers')
def on_create_jobtracer(spec, name, namespace, logger, **kwargs):

    logger.info("Created or updating a JobTracer ")

    existing_tracker_object = get_namespace_object(namespace)

    # If no existing item
    # This is a new namespace to track request
    # Add to the list
    if existing_tracker_object is None:
        logger.info(f"Adding new namespace: {namespace} to list. Will track jobs.")
        namespaces_to_trace.append({
            "namespace": namespace,
            "spec": spec
        })
    else:
        logger.info(f"A JobTracer already exists for namespace: {namespace}. Will replace config")
        logger.info(f"JobTracer for {namespace} replaced {existing_tracker_object['spec']} with {spec}")
        existing_tracker_object['spec'] = spec
    
    logger.info(namespaces_to_trace)
    logger.info("-"*30)

# A JobTracer has been deleted
# Remove from the list
@kopf.on.delete('jobtracers')
def on_delete_jobtracer(spec, name, namespace, logger, **kwargs):
    logger.info(f"Deleted a jobtracer. Namespace is {namespace}")

    existing_tracker_object = get_namespace_object(namespace)
    
    if existing_tracker_object is not None:
        logger.info(f"tracking list before remove: {namespaces_to_trace}")
        namespaces_to_trace.remove(existing_tracker_object)
    logger.info(f"tracking list after remove: {namespaces_to_trace}")
    logger.info("+"*30)