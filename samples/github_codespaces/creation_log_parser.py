from datetime import datetime, timedelta
import subprocess
import secrets

OTEL_COLLECTOR_URL_HTTP = "http://localhost:4318"
SERVICE_NAME = "codespace-tracking"
activity_list = []
#with open("creation.log", mode="r") as log:
with open("/workspaces/.codespaces/.persistedshare/creation.log", mode="r") as log:
    loglines = log.readlines()

    for line in loglines:

        # All "starting activity" lines end with 3 dots
        # Except the final line which is a one-off exception
        # =================================================================================
        if "..." in line or "Finished configuring codespace." in line:
            activity_list.append(line.strip())

log_start_time = activity_list[0][:24]
#print(f"Aside from dumping generic info, log started at: {log_start_time}")

trace_id = secrets.token_hex(16)
main_span_id = secrets.token_hex(8)
trace_start_time = None
trace_end_time = None

position = 0

sub_spans_to_send = []

#print(f"Activity list len: {len(activity_list)}")
for activity in activity_list:
    # We need to get two activities to create the span
    # Start and end
    # Imagine this:
    # 2024-06-03 11:24:45.950Z Configuration starting...
    # 2024-06-03 11:24:49.377Z Creating container...
    #
    # Here we need to know that "Configuration starting..." began at 11:24:45.950Z
    # Ended at 11:24:49.377Z (so duration was 573ms)
    #
    activity_start_left, activity_start_right = activity[:24], activity[26:]

    activity_start_left_dt = datetime.fromisoformat(activity_start_left)
    
    # Set trace start time
    if trace_start_time is None: trace_start_time = activity_start_left_dt
    if trace_end_time is None and position == len(activity_list)-1: trace_end_time = activity_start_left_dt + timedelta(seconds=1)

    try:
        activity_end_left = activity_list[position+1][:24]
        activity_end_left_dt = datetime.fromisoformat(activity_end_left)

        diff = activity_end_left_dt - activity_start_left_dt

        sub_spans_to_send.append({
            "trace-id": trace_id,
            "span-id": secrets.token_hex(8),
            "parent-span-id": main_span_id,
            "start-time": activity_start_left_dt,
            "end-time": activity_end_left_dt,
            "span-name": activity_start_right,
            "duration-seconds": diff.total_seconds()
        })
    except:
        main_span_length_seconds = (trace_end_time - trace_start_time).total_seconds()
        start_time = str(int(trace_start_time.timestamp()*1000000000))
        duration = str(int(main_span_length_seconds*1000))
        args = [
            "tracepusher",
            "--endpoint", OTEL_COLLECTOR_URL_HTTP,
            "--insecure", "true",
            "--service-name", SERVICE_NAME,
            "--span-name", "codespace-creation",
            "--start-time", start_time,
            "--duration", duration,
            "--duration-type", "ms",
            "--trace-id", trace_id,
            "--span-id", secrets.token_hex(8)
        ]
        output = subprocess.run(args, capture_output=True, text=True)
    
    position += 1

# Now send sub spans
for span in sub_spans_to_send:
    start_time = str(int(span['start-time'].timestamp()*1000000000))
    span_name = span['span-name']
    span_parent_id = span['parent-span-id']

    args = [
        "tracepusher",
        "--endpoint", OTEL_COLLECTOR_URL_HTTP,
        "--insecure", "true",
        "--service-name", SERVICE_NAME,
        "--span-name", span_name,
        "--start-time", start_time,
        "--duration", str(int(span['duration-seconds']*1000)),
        "--duration-type", "ms",
        "--trace-id", span['trace-id'],
        "--span-id", span['span-id'],
        "--parent-span-id", span_parent_id
    ]

    # Send spans to OTEL collector
    subprocess.run(args, capture_output=True, text=True)
