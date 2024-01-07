import sys
import requests
import time
import secrets
import argparse
import datetime

# This script is very simple. It does the equivalent of:
# curl -i -X POST http(s)://endpoint/v1/traces \
# -H "Content-Type: application/json" \
# -d @trace.json

#############################################################################
# USAGE
# python tracepusher.py -ep=http(s)://localhost:4318 -sen=serviceNameA -spn=spanX -dur=2
#############################################################################

# Modified from: https://stackoverflow.com/a/11111177/9997385
def unix_time_millis(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    # This looks odd but the .0f means no decimal places
    # Then appending 000 makes the string 19 chars long like:
    # 1700967916494000000
    return '{:.0f}000'.format((dt - epoch).total_seconds() * 1000000)

# Minimum
# offsetInMillis=name=key=value
# In which case:
# - timestamp of event is + offset by milliseconds given in input from start_time_nanos_since_epoch
# - value type is assumed to be string
#
# offsetInMillis=name=key=value=valueType
# 0=event1=userID=23=intValue
def get_span_events_list(args, start_time_nanos_since_epoch):
  
  event_list = []
  dropped_event_count = 0
  
  if args == None or len(args) < 1:
     return event_list, dropped_event_count
  
  for item in args:
    # How many = are in the item?
    # <3 = invalid item. Ignore
    # 3 = offsetInMillis=name=key=value (tracepusher assumes type=stringValue)
    # 4 = offsetInMillis=name=key=value=type (user is explicitly telling us the type. tracepusher uses it)
    # >4 = invalid item. Ignore
    number_of_equals = item.count("=")
    if number_of_equals != 3 and number_of_equals != 4:
        dropped_event_count += 1
        continue
    
    offset_millis = 0
    event_name = ""
    event_key = ""
    event_value = ""
    event_type = "stringValue"
    dropped_event_count = 0

    if number_of_equals != 3 and number_of_equals != 4:
        dropped_event_count += 1
    
    if number_of_equals == 3:
        offset_millis_string, event_name, event_key, event_value = item.split("=", maxsplit=3)
        offset_millis = int(offset_millis_string)
        # User did not pass a type. Assuming type == 'stringValue'
    
    if number_of_equals == 4:
        offset_millis_string, event_name, event_key, event_value, event_type = item.split('=',maxsplit=4)
        offset_millis = int(offset_millis_string)
        # User passed an explicit type. Tracepusher will use it.

    # calculate event time
    # millis to nanos
    offset_nanos = offset_millis * 1000000
    event_time = start_time_nanos_since_epoch + offset_nanos

    event_list.append({
       "timeUnixNano": event_time,
       "name": event_name,
       "attributes": [{
          "key": event_key,
          "value": {
             event_type: event_value
          }
       }]
    })

  return event_list, dropped_event_count

# Returns attributes list:
# From spec: https://opentelemetry.io/docs/concepts/signals/traces/#attributes
# Syntax: {
#           "key": "my.scope.attribute",
#           "value": {
#             "stringValue": "some scope attribute"
#           }
#         }
# Ref: https://github.com/open-telemetry/opentelemetry-proto/blob/9876ebfc5bcf629d1438d1cf1ee8a1a4ec21676c/examples/trace.json#L20-L56
# Values must be a non-null string, boolean, floating point value, integer, or an array of these values
# stringValue, boolValue, intValue, doubleValue, arrayValue, kvlistValue, bytesValue are all valid
def get_span_attributes_list(args):

    arg_list = []
    dropped_attribute_count = 0

    if args == None or len(args) < 1:
        return arg_list, dropped_attribute_count

    for item in args:
        # How many = are in the item?
        # 0 = invalid item. Ignore
        # 1 = key=value (tracepusher assumes type=stringValue)
        # 2 = key=value=type (user is explicitly telling us the type. tracepusher uses it)
        # >3 = invalid item. tracepusher does not support span keys and value containing equals. Ignore.
        number_of_equals = item.count("=")
        if number_of_equals == 0 or number_of_equals > 2:
           dropped_attribute_count += 1
           continue

        key = ""
        value = ""
        type = "stringValue"

        if number_of_equals == 1:
            key, value = item.split("=", maxsplit=1)
            # User did not pass a type. Assuming type == 'stringValue'
        
        if number_of_equals == 2:
            key, value, type = item.split('=',maxsplit=2)
            # User passed an explicit type. Tracepusher will use it.

        arg_list.append({"key": key, "value": { type: value}})
    
    return arg_list, dropped_attribute_count

def process_span_kind(input):
  valid_values = [
     "UNSPECIFIED",
     "INTERNAL",
     "CLIENT",
     "SERVER",
     "CONSUMER",
     "PRODUCER"
  ]
  output = ""
  output = input.upper()
  # If span kind is not valid
  # Maintain backwards compatibility
  # Default to SPAN_KIND_INTERNAL
  # If span kind is set to unspecified
  # Default (as per OTEL spec) to INTERNAL
  if output not in valid_values:
    output = ""
  elif output == "UNSPECIFIED":
     output = "SPAN_KIND_INTERNAL"
  else:
     output = f"SPAN_KIND_{output}"
  
  return output

def check_duration_type(input):
   valid_values = [ "ms", "s" ]

   if input.lower() in valid_values:
      return True
   else:
      return False

def get_span_status_int(input):
  if input.lower() == "ok":
    return 1
  if input.lower() == "error":
    return 2
  return 0

parser = argparse.ArgumentParser()

# Notes:
# You can use either short or long (mix and match is OK)
# Hyphens are replaced with underscores hence for retrieval
# and leading hyphens are trimmed
# --span-name becomes args.span_name
# Retrieval also uses the second parameter
# Hence args.dry_run will work but args.d won't
parser.add_argument('-ep', '--endpoint', required=True)
parser.add_argument('-sen','--service-name', required=True)
parser.add_argument('-spn', '--span-name', required=True)
parser.add_argument('-dur', '--duration', required=True, type=int)
parser.add_argument('-dt', '--duration-type', required=False, default="s")
parser.add_argument('-dr','--dry-run','--dry', required=False, default="False")
parser.add_argument('-x', '--debug', required=False, default="False")
parser.add_argument('-ts', '--time-shift', required=False, default="False")
parser.add_argument('-psid','--parent-span-id', required=False, default="")
parser.add_argument('-tid', '--trace-id', required=False, default="")
parser.add_argument('-sid', '--span-id', required=False, default="")
parser.add_argument('-spnattrs', '--span-attributes', required=False, nargs='*')
parser.add_argument('-spnevnts', '--span-events', required=False, nargs='*')
parser.add_argument('-sk', '--span-kind', required=False, default="INTERNAL")
parser.add_argument('-ss', '--span-status', required=False, default="OK")
parser.add_argument('-insec', '--insecure', required=False, default="False")
parser.add_argument('-st', '--start-time', required=False, default="")

args = parser.parse_args()

endpoint = args.endpoint
service_name = args.service_name
span_name = args.span_name
duration = args.duration
duration_type = args.duration_type
dry_run = args.dry_run
debug_mode = args.debug
time_shift = args.time_shift
parent_span_id = args.parent_span_id
trace_id = args.trace_id
span_id = args.span_id
span_kind = args.span_kind
span_status = get_span_status_int(args.span_status)
allow_insecure = args.insecure
start_time = args.start_time

span_attributes_list, dropped_attribute_count = get_span_attributes_list(args.span_attributes)
span_kind = process_span_kind(span_kind)
if span_kind == "":
   sys.exit("Error: invalid span kind provided.")

duration_type_valid = check_duration_type(duration_type)
if not duration_type_valid:
   sys.exit("Error: Duration Type invalid. Try `ms` for milliseconds or `s` for seconds")

# Debug mode required?
DEBUG_MODE = False
if debug_mode.lower() == "true":
   print("> Debug mode is ON")
   DEBUG_MODE = True

DRY_RUN = False
if dry_run.lower() == "true":
   print("> Dry run mode is ON. Nothing will actually be sent.")
   DRY_RUN = True

TIME_SHIFT = False
if time_shift.lower() == "true":
  print("> Time shift enabled. Will shift the start and end time back in time by DURATION seconds.")
  TIME_SHIFT = True

HAS_PARENT_SPAN = False
if parent_span_id != "":
  print(f"> Pushing a child (sub) span with parent span id: {parent_span_id}")
  HAS_PARENT_SPAN = True

# Prior to v1.0
# This flag will ONLY print a soft WARNING
# If the flag is False (explicitly or omitted)
# a warning is given that in v1.0 calls to http:// endpoints
# will FAIL if "--insecure true" is NOT set
#
# In other words, prior to v1.0 no breaking change
# v1.0 and above, if a user wishes to send to an http:// endpoint
# --insecure true MUST be set
#
# Best practice: Start setting this flag now!

# First convert to boolean
ALLOW_INSECURE = False
if allow_insecure.lower() == "true":
  ALLOW_INSECURE = True

# TODO: Adjust this error message for >=v1.0
# From v1.0 make this WARN only appear in DEBUG_MODE
if not ALLOW_INSECURE:
  print("WARN: --insecure flag is omitted or is set to false. Prior to v1.0 tracepusher still works as expected (span is sent). In v1.0 and above, you MUST set '--insecure true' if you want to send to an http:// endpoint. See https://github.com/agardnerIT/tracepusher/issues/78")

# If user has explicitly provided a start time:
# 1) It must be in the following format:
#    2023-11-26T03:05:16.494Z
#    yyyy-mm-ddThh:mm:ss.mssTZ
# 3) Convert to millis since epoch
# eg. 1700931916494
# 4) Further converter to nanos (eg. + 9 zeros)
# eg. 1700931916494000000

HAS_START_TIME = False
start_time_nanos_since_epoch = 0

if start_time != "":
    HAS_START_TIME = True
    print("Got an explicit start time")
    # TODO: Validate start_time format and default to "now" if not set correctly.
    # The ONLY input formats tracepusher currently supports are:
    # 1) A 19 digit string representing milliseconds since the epoch: eg. 1700967916494000000
    # 2) "%Y-%m-%dT%H:%M:%S.%fZ" eg. "2023-11-26T03:05:16.844Z"

    if len(start_time) == 19:
        # Try to cast input to an int
        # If an exception is caught, the user maybe tried to pass another 19 digit string like...
        # "2023-11-26T03:05:16". This is NOT supported!
        try:
            start_time_nanos_since_epoch = int(start_time)
        except:
            HAS_START_TIME = False
            print("WARN: --start-time was in an invalid format. Trace will be sent but start time will default to 'now'.")
    else:
        try:
            start_time_nanos_since_epoch = unix_time_millis(datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ'))
        except:
            print("WARN: --start-time value was in an incorrect format. Valid formats: 1) 19 digit integer representing millis since epoch 2) '%Y-%m-%dT%H:%M:%S.%fZ' eg. '2023-11-26T03:05:16.844Z'. Trace will be send with start_time of now.")
            # The provided start time had an invalid value, so fallback to the trace having a start time of "now"
            HAS_START_TIME = False

if DEBUG_MODE:
  print(f"Endpoint: {endpoint}")
  print(f"Service Name: {service_name}")
  print(f"Span Name: {span_name}")
  print(f"Duration: {duration}")
  print(f"Duration Type: {duration_type}")
  print(f"Dry Run: {type(dry_run)} = {dry_run}")
  print(f"Debug: {type(debug_mode)} = {debug_mode}")
  print(f"Time Shift: {type(time_shift)} = {time_shift}")
  print(f"Parent Span ID: {parent_span_id}")
  print(f"Trace ID: {trace_id}")
  print(f"Span ID: {span_id}")
  print(f"Dropped Attribute Count: {dropped_attribute_count}")
  print(f"Span Kind: {span_kind}")
  print(f"Span Status: {span_status}")
  print(f"Allow insecure endpoints: {allow_insecure}")
  print(f"Provided start time: {start_time}. Nanos since epoch: {start_time_nanos_since_epoch}")

# disable until v1.0
#if endpoint.startswith("http://") and not ALLOW_INSECURE:
#  print("ERROR: Endpoint is http:// (insecure). You MUST set '--insecure true'. Span has NOT been sent.")
#  sys.exit(1)

# Generate random chars for trace and span IDs
# of 32 chars and 16 chars respectively
# per secrets documentation
# each byte is converted to two hex digits
# hence this "appears" wrong by half but isn't
# If this is a child span, we already have a trace_id and parent_span_id
# So do not generate

if trace_id == "":
  trace_id = secrets.token_hex(16)
if len(trace_id) != 32:
  sys.exit("Error: trace_id should be 32 characters long!")

if span_id == "":
  span_id = secrets.token_hex(8)
if len(span_id) != 16:
  sys.exit("Error: span_id should be 16 characters long!")

if DEBUG_MODE:
  print(f"Trace ID: {trace_id}")
  print(f"Span ID: {span_id}")
  print(f"Parent Span ID: {parent_span_id}")

duration_nanos = 0
if duration_type == "ms":
   duration_nanos = duration * 1000000 # ms to ns
elif duration_type == "s":
   duration_nanos = duration * 1000000000 # s to ns

if not HAS_START_TIME:
    # get time now
    start_time_nanos_since_epoch = time.time_ns()

# calculate future time by adding that many nanoseconds
time_future = int(start_time_nanos_since_epoch) + duration_nanos

# shift start_time_nanos_since_epoch and time_future back by duration 
if not HAS_START_TIME and TIME_SHIFT:
   start_time_nanos_since_epoch = start_time_nanos_since_epoch - duration_nanos
   time_future = time_future - duration_nanos

if DEBUG_MODE:
   print(f"Time shifted? {TIME_SHIFT}")
   print(f"Start time: {start_time_nanos_since_epoch}")
   print(f"Time future: {time_future}")

# Now that the right start / end time is available
# process any span events
span_events_list, dropped_event_count = get_span_events_list(args.span_events, start_time_nanos_since_epoch)

if DEBUG_MODE:
   print("Printing Span Events List:")
   print(span_events_list)
   print("-----")
   print(f"Dropped Span Events Count: {dropped_event_count}")

trace = {
 "resourceSpans": [
   {
     "resource": {
       "attributes": [
         {
           "key": "service.name",
           "value": {
             "stringValue": service_name
           }
         }
       ]
     },
     "scopeSpans": [
       {
         "scope": {
           "name": "manual-test"
         },
         "spans": [
           {
             "traceId": trace_id,
             "spanId": span_id,
             "name": span_name,
             "kind": span_kind,
             "start_time_unix_nano": start_time_nanos_since_epoch,
             "end_time_unix_nano": time_future,
             "droppedAttributesCount": dropped_attribute_count,
             "attributes": span_attributes_list,
             "events": span_events_list,
             "droppedEventsCount": dropped_event_count,
             "status": {
               "code": span_status
             }
           }
         ]
       }
     ]
   }
 ]
}

if HAS_PARENT_SPAN:
  # Add parent_span_id field
  trace['resourceSpans'][0]['scopeSpans'][0]['spans'][0]['parentSpanId'] = parent_span_id

if DEBUG_MODE:
   print("Trace:")
   print(trace)

if DRY_RUN:
   print(f"Collector URL: {endpoint}. Service Name: {service_name}. Span Name: {span_name}. Trace Length ({duration_type}): {duration}")
   # Only print if also not running in DEBUG_MODE
   # Otherwise we get a double print
   if not DEBUG_MODE:
     print("Trace:")
     print(trace)
   
if not DRY_RUN:
  resp = requests.post(
     f"{endpoint}/v1/traces", 
     headers={ "Content-Type": "application/json" }, 
     json=trace,
     timeout=5 
     )
  print(resp)