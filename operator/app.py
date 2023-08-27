from kubernetes import client, config, watch
import time
from datetime import datetime, timezone
import subprocess

######
# DISCLAIMER
# This is still a work in progress
# Progress is being tracked here: https://github.com/agardnerIT/tracepusher/issues/71
# Get involved! We need your help to take this across the line!
#
# TODO: LOTS! Almost everything here is fragile, hardcoded and can be improved
# This is very much still POC code.
######

SCRIPT_START_TIME_UTC = datetime.now(timezone.utc)

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

target_namespaces = ["default"]

w = watch.Watch()

v1 = client.BatchV1Api()


# Watch all k8s "Jobs" in "default" namespace
# TODO: generalise this to target any namespace (see target_namespaces above)
for event in w.stream(v1.list_namespaced_job, namespace="default"):

    job = event['object']

    job_name = job.metadata.name

    # This check is in anticipation of moving away from
    # list_namespaced_job to a more general (multi-namespace) stream method
    # When that happens, the NS will need to be filtered
    if job.metadata.namespace not in target_namespaces: continue

    # If job has a completion time (finish time)
    # Then use it
    # If a job does NOT have a completion time
    # We must use the start time
    # as it's the only thing we know
    # 
    # Either way, store as known_time
    known_time = None
    if job.status.completion_time is not None:
        known_time = job.status.completion_time
    elif job.status.start_time is not None:
        # No completion_time, so fallback to start time
        known_time = job.status.start_time
    else:
        print(f"No known time for job. This happens when job is first put in queue and waiting to start. Skipping {job_name}. This is not an error.")
        continue

    # If the event time was before
    # start of script
    # do not push
    # This might seem to cause "currently in-flight" events
    # not to be pushed, but remember, another event is sent
    # when the event finishes
    # The new event will have a known_time > SCRIPT_START_TIME_UTC
    if known_time < SCRIPT_START_TIME_UTC:
        print(f"This event happened before script start time. Ignoring {job_name}")
        continue

    if job.status.start_time is not None:
        ##############################################
        # Failed job
        # Failed jobs do not have a completion_time
        # Assume a 1s duration
        ##############################################
        if job.status.completion_time is None and job.status.failed is not None:

            # Get backofflimit
            # k8s defaults to 6
            backoff_limit = job.spec.backoff_limit

            print("JOB FAILED")
            print(f"Job will retry {backoff_limit} times.")

            job_status = "Failed"
            # This will increment up to will_retry_count
            attempt_number = job.status.failed
            duration = 1

            number_of_containers_in_job = len(job.spec.template.spec.containers)

            # Backoff limit reached
            # Add extra error message
            # Which will now be there
            # backoff_limit is zero indexed
            # meaning final attempt_number will always be backoff_limit+1
            if attempt_number > backoff_limit:
                print("Backoff Limit reached")
                print(job.status)
                failure_message = job.status.conditions[0].message
                failure_reason = job.status.conditions[0].reason

                tracepusher_cmd = [
                    "python3",
                    "tracepusher.py",
                    "-ep",
                    "http://localhost:4318",
                    "-sen",
                    "k8s",
                    "-spn",
                    f"{job_name}",
                    "-dur",
                    f"{duration}",
                    "--span-status",
                    "ERROR",
                    "--time-shift",
                    "true",
                    "-spnattrs",
                    "type=job",
                    f"namespace={job.metadata.namespace}",
                    f"container_count={number_of_containers_in_job}",
                    f"attempt_number={attempt_number}",
                    f"backoff_limit={backoff_limit}",
                    f"backoff_limit_reached=true",
                    f"jobstatus={job.status}",
                    f"failure_message={failure_message}",
                    f"failure_reason={failure_reason}"
                ]

                # Read pod logs for job to get proper failure info
                api_instance = client.CoreV1Api()
                job_pods = api_instance.list_namespaced_pod(namespace="default", label_selector=f"job-name={job_name}")

                print(f"GOT SOME PODS FOR JOB: {job_name}")
                for pod in job_pods.items:
                    print(pod)

                    # for each container in pod
                    # get container name + error code
                    for container_status in pod.status.container_statuses:
                        tracepusher_cmd.append(f"container-{container_status.name}-reason={container_status.state.terminated.reason}")
                        tracepusher_cmd.append(f"container-{container_status.name}-exitcode={container_status.state.terminated.exit_code}")
                        tracepusher_cmd.append(f"container-{container_status.name}-message={container_status.state.terminated.message}")
                        print(f"Container Name: {container_status.name} - Reason: {container_status.state.terminated.reason} - Exit Code: {container_status.state.terminated.exit_code} - Message: {container_status.state.terminated.message}")


                # Call tracepusher
                subprocess.call(tracepusher_cmd)

        #########################################
        # Successful job
        #########################################
        if job.status.completion_time is not None:
            
            print(f"{job_name} finished successfully!")
            print(f"Start Time: {job.status.start_time}")
            print(f"Finish Time: {job.status.completion_time}")
            duration = int((job.status.completion_time - job.status.start_time).total_seconds())
            print(f"Job duration: {duration}s")

            number_of_containers_in_job = len(job.spec.template.spec.containers)
            print(number_of_containers_in_job)

            # Call tracepusher
            subprocess.call([
                "python3",
                "tracepusher.py",
                "-ep",
                "http://localhost:4318",
                "-sen",
                "k8s",
                "-spn",
                job_name,
                "-dur",
                f"{duration}",
                "--span-status",
                "OK",
                "--time-shift",
                "true",
                "-spnattrs",
                "type=job",
                f"namespace={job.metadata.namespace}",
                f"container_count={number_of_containers_in_job}"
                ])
