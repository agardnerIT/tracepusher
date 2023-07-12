import sys
import requests
import time
import secrets
import argparse

# This script is very simple. It does the equivalent of:
# curl -i -X POST http(s)://endpoint/v1/traces \
# -H "Content-Type: application/json" \
# -d @trace.json

#############################################################################
# USAGE
# python tracepusher.py -ep=http(s)://localhost:4318 -sen=serviceNameA -spn=spanX -dur=2
#############################################################################

# Minimum
# offsetInMillis=name=key=value
# In which case:
# - timestamp of event is + offset by milliseconds given in input from time_now
# - value type is assumed to be string
#
# offsetInMillis=name=key=value=valueType
# 0=event1=userID=23=intValue
def get_span_events_list(args, time_now):
  
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
    event_time = time_now + offset_nanos

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
parser.add_argument('-dr','--dry-run','--dry', required=False, default="False")
parser.add_argument('-x', '--debug', required=False, default="False")
parser.add_argument('-ts', '--time-shift', required=False, default="False")
parser.add_argument('-psid','--parent-span-id', required=False, default="")
parser.add_argument('-tid', '--trace-id', required=False, default="")
parser.add_argument('-sid', '--span-id', required=False, default="")
parser.add_argument('-spnattrs', '--span-attributes', required=False, nargs='*')
parser.add_argument('-spnevnts', '--span-events', required=False, nargs='*')

args = parser.parse_args()

endpoint = args.endpoint
service_name = args.service_name
span_name = args.span_name
duration = args.duration
dry_run = args.dry_run
debug_mode = args.debug
time_shift = args.time_shift
parent_span_id = args.parent_span_id
trace_id = args.trace_id
span_id = args.span_id

span_attributes_list, dropped_attribute_count = get_span_attributes_list(args.span_attributes)

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

if DEBUG_MODE:
  print(f"Endpoint: {endpoint}")
  print(f"Service Name: {service_name}")
  print(f"Span Name: {span_name}")
  print(f"Duration: {duration}")
  print(f"Dry Run: {type(dry_run)} = {dry_run}")
  print(f"Debug: {type(debug_mode)} = {debug_mode}")
  print(f"Time Shift: {type(time_shift)} = {time_shift}")
  print(f"Parent Span ID: {parent_span_id}")
  print(f"Trace ID: {trace_id}")
  print(f"Span ID: {span_id}")
  print(f"Dropped Attribute Count: {dropped_attribute_count}")

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

duration_nanos = duration * 1000000000
# get time now
time_now = time.time_ns()
# calculate future time by adding that many seconds
time_future = time_now + duration_nanos

# shift time_now and time_future back by duration 
if TIME_SHIFT:
   time_now = time_now - duration_nanos
   time_future = time_future - duration_nanos

if DEBUG_MODE:
   print(f"Time shifted? {TIME_SHIFT}")
   print(f"Time now: {time_now}")
   print(f"Time future: {time_future}")

# Now that the right start / end time is available
# process any span events
span_events_list, dropped_event_count = get_span_events_list(args.span_events, time_now)

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
             "kind": "SPAN_KIND_INTERNAL",
             "start_time_unix_nano": time_now,
             "end_time_unix_nano": time_future,
             "droppedAttributesCount": dropped_attribute_count,
             "attributes": span_attributes_list,
             "events": span_events_list,
             "droppedEventsCount": dropped_event_count,
             "status": {
               "code": 1
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
   print(f"Collector URL: {endpoint}. Service Name: {service_name}. Span Name: {span_name}. Trace Length (seconds): {duration}")
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