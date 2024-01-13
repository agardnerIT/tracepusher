import json
import math
import subprocess
import secrets
import argparse
import sys
import semver

HAR_TO_OTEL_VERSION="0.10.0"

##### Start input processing

parser = argparse.ArgumentParser()

parser.add_argument('-f','--file', required=True, default="")
parser.add_argument('-ep','--endpoint', required=True, default="")
parser.add_argument('-insec', '--insecure', required=False, default="False")
parser.add_argument('-sen', '--service-name', required=False, default="har-to-otel")
parser.add_argument('-t','--timings', required=False, default="True")
parser.add_argument('-reqh','--request-headers', required=False, default="False")
parser.add_argument('-resph','--response-headers', required=False, default="False")
parser.add_argument('-reqc','--request-cookies', required=False, default="False")
parser.add_argument('-respc','--response-cookies', required=False, default="False")
parser.add_argument('-x','--debug', required=False, default="False")
parser.add_argument('-dr','--dry-run','--dry', required=False, default="False")
parser.add_argument('-v', '--version', action="version", version=HAR_TO_OTEL_VERSION)

args = parser.parse_args()

file_to_load = args.file
endpoint = args.endpoint
allow_insecure = args.insecure
service_name = args.service_name
add_timings = args.timings
add_request_headers = args.request_headers
add_response_headers = args.response_headers
add_request_cookies = args.request_cookies
add_response_cookies = args.response_cookies
debug_mode = args.debug
dry_run = args.dry_run

# Check a file is provided
if file_to_load == "":
    sys.exit("ERROR: You must provide the path to a .har file")

# Check a file is provided
if endpoint == "":
    sys.exit("ERROR: You must provide the OpenTelemetry collector endpoint eg. https://localhost:4318")

ALLOW_INSECURE = False
if allow_insecure.lower() == "true":
  ALLOW_INSECURE = True

# If insecure collector endpoints are disallowed
# and the collector endpoint IS insecure
# fail with an error
if not ALLOW_INSECURE and endpoint.startswith("http://"):
    sys.exit("ERROR: An insecure collector endpoint has been provided and the --insecure flag is not set OR set to --insecure false. To enable insecure endpoints, set --insecure true")
# Add timings?
ADD_TIMINGS = True
if add_timings.lower() == "false":
    ADD_TIMINGS = False

# Add request headers?
ADD_REQUEST_HEADERS = False
if add_request_headers.lower() == "true":
    ADD_REQUEST_HEADERS = True
# Add response headers?
ADD_RESPONSE_HEADERS = False
if add_response_headers.lower() == "true":
    ADD_RESPONSE_HEADERS = True

# Add request cookies?
ADD_REQUEST_COOKIES = False
if add_request_cookies.lower() == "true":
    ADD_REQUEST_COOKIES = True
# Add response cookies?
ADD_RESPONSE_COOKIES = False
if add_response_cookies.lower() == "true":
    ADD_RESPONSE_COOKIES = True

# Debug mode required?
DEBUG_MODE = False
if debug_mode.lower() == "true":
   print("> Debug mode is ON")
   DEBUG_MODE = True

# Dry run mode enabled?
DRY_RUN = False
if dry_run.lower() == "true":
   print("> Dry run mode is ON. Nothing will actually be sent.")
   DRY_RUN = True

###### End input processing

if DEBUG_MODE:
    print(f"HAR File: {file_to_load}")
    print(f"Endpoint: {endpoint}")
    print(f"Allow insecure collector endpoint: {ALLOW_INSECURE}")
    print(f"Add timings? {ADD_TIMINGS}")
    print(f"Add request headers? {ADD_REQUEST_HEADERS}")
    print(f"Add response headers? {ADD_RESPONSE_HEADERS}")
    print(f"Add request cookies? {ADD_REQUEST_COOKIES}")
    print(f"Add response cookies? {ADD_RESPONSE_COOKIES}")
    print(f"Debug mode: {DEBUG_MODE}")
    print(f"Service name: {service_name}")
    print(f"Dry run mode: {DRY_RUN}")

# Credit: https://stackoverflow.com/a/14822210
def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1000)))
   p = math.pow(1000, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def run_tracepusher(args=""):
    # Try to run tracepusher binary
    # Also ensure that tracepusher is at version 0.10.0 or above (required for --start-time flag)
    # If error occurs, tracepusher is not in the path
    # fallback to tracepusher.py in current directory

    print(f"ARGS TO TRACEPUSHER: {args}")

    tracepusher_output = ""

    # first try the local copy
    # if that fails or is the wrong version, try the path version
    TRACEPUSHER_TRY_PATH = False
    try:
        tracepusher_output = subprocess.run(f"python3 tracepusher.py --version", capture_output=True, shell=True, text=True)
        if tracepusher_output.returncode != 0: # This will happen if tracepusher is available but version < 0.10.0 ie. doesn't have --version flag
            TRACEPUSHER_TRY_PATH = True
    except:
        TRACEPUSHER_TRY_PATH = True
    
    if not TRACEPUSHER_TRY_PATH: # local tracepusher is the correct version
        print("Local tracepusher.py is the correct version. Use it.")
        try:
            tracepusher_output = subprocess.run(f"python3 tracepusher.py {args}" , capture_output=True, shell=True, text=True)
        except:
            print("Exception caught running local tracepusher.py")
    else: # trying standalone tracepusher
        # Local tracepusher.py missing or < 0.10.0. Try path...
        try:
            tracepusher_output = subprocess.run(f"tracepusher --version", capture_output=True, shell=True, text=True)

            if tracepusher_output.returncode == 0:
                # Path tracepusher is a suitable version. Use it
                tracepusher_output = subprocess.run(f"tracepusher {args}" , capture_output=True, shell=True, text=True)
            else:
                raise Exception("Cannot find a valid (>= v0.10.0) copy of tracepusher locally or in PATH. Nothing has been sent. Cannot continue. Exiting.")
        except:
            print("ERROR: Cannot find a valid (>= v0.10.0) copy of tracepusher locally or in PATH. Nothing has been sent. Cannot continue. Exiting.")
            exit(1)

    return tracepusher_output

with open(file=file_to_load, mode="r") as har_file:
    har_content = har_file.read()
    har_json = json.loads(har_content)

page_and_items_array = []

for page in har_json['log']['pages']:

    page_name = page['title']
    page_ref = page['id']
    page_timings = page['pageTimings']

    new_entry = {
        "page_ref": page_ref,
        "page_name": page_name,
        "pageTimings": page_timings,
        "items": []
    }

    for loaded_item in har_json['log']['entries']:
        item_page_ref = loaded_item['pageref']

        if item_page_ref == page_ref:
            new_entry['items'].append(loaded_item)
    
    page_and_items_array.append(new_entry)

for page in page_and_items_array:

    # Generate a new trace_id for each page
    trace_id = secrets.token_hex(16)
    page_ref = page['page_ref']
    page_name = page['page_name']
    item_count_for_page = len(page['items'])

    if DEBUG_MODE:
        print("-- Processing page --")
        print(f"{page_ref} | {page_name} | Items: {item_count_for_page}")
    
    for loaded_item in page['items']:
        item_page_ref = loaded_item['pageref']
        item_name = loaded_item['request']['url']

        ui_time_dev_tools = round(loaded_item['time']) - round(loaded_item['timings']['_blocked_queueing'])
        span_attributes = ""

        if page_ref == item_page_ref and item_name == page_name:
            if DEBUG_MODE:
                print(f"Adding pageTimings to {item_page_ref} which matches {page_ref} ({loaded_item['request']['url']})")

            for key in page['pageTimings']:
                span_attributes += f"{key}={page['pageTimings'][key]} "
        
        # Add items from top level
        span_attributes += f"serverIPAddress='{loaded_item['serverIPAddress']}' "
        # Add request details
        span_attributes += f"request.method={loaded_item['request']['method']} "
        span_attributes += f"request.httpVersion={loaded_item['request']['httpVersion']} "
        # Add request headers
        if ADD_REQUEST_HEADERS:
            if DEBUG_MODE:
                print(f"Adding request headers for {item_name}")

            for header in loaded_item['request']['headers']:
                dirty_header_value = header['value']
                clean_header_value = dirty_header_value.replace('\"','')
                span_attributes += f"request.headers.{header['name']}=\"{clean_header_value}\" "
        # Add request cookies
        if ADD_REQUEST_COOKIES:
            if DEBUG_MODE:
                print(f"Adding request cookies for {item_name}")

            for cookie in loaded_item['request']['cookies']:
                cookie_name = cookie['name']

                for key in cookie.keys():
                    span_attributes += f"request.cookies.cookie.{cookie_name}.{key}=\"{cookie[key]}\" "

        # Add response details
        span_attributes += f"response.status={loaded_item['response']['status']} "
        span_attributes += f"response.statusText=\"{loaded_item['response']['statusText']}\" "
        span_attributes += f"response.httpVersion={loaded_item['response']['httpVersion']} "
        span_attributes += f"response.content.size={loaded_item['response']['content']['size']} "
        span_attributes += f"response._transferSize={loaded_item['response']['_transferSize']} "
        # Add response headers
        if ADD_RESPONSE_HEADERS:
            if DEBUG_MODE:
                print(f"Adding response headers for {item_name}")

            for header in loaded_item['response']['headers']:
                dirty_header_value = header['value']
                clean_header_value = dirty_header_value.replace('\"','')
                span_attributes += f"response.headers.{header['name']}=\"{clean_header_value}\" "
        
        # Add request cookies
        if ADD_RESPONSE_COOKIES:
            if DEBUG_MODE:
                print(f"Adding response cookies for {item_name}")

            for cookie in loaded_item['response']['cookies']:
                cookie_name = cookie['name']

                for key in cookie.keys():
                    span_attributes += f"response.cookies.cookie.{cookie_name}.{key}=\"{cookie[key]}\" "

        # Add timings
        if ADD_TIMINGS:
            if DEBUG_MODE:
                print(f"Adding timings for {item_name}")
            for key in loaded_item['timings']:
                span_attributes += f"timings.{key}={loaded_item['timings'][key]} "

        span_id = secrets.token_hex(8)

        print(f"START TIME: {loaded_item['startedDateTime']}")
        args = f"--endpoint {endpoint} --insecure {str(ALLOW_INSECURE).lower()} --service-name {service_name} --span-name '{loaded_item['request']['url']}' --duration {int(ui_time_dev_tools)} --duration-type 'ms' --trace-id {trace_id} --span-id {span_id} --start-time '{loaded_item['startedDateTime']}' --span-attributes {span_attributes} --debug {DEBUG_MODE} --dry-run {DRY_RUN}"
        
        if DEBUG_MODE:
            print(f"Args: {args}")
        # Run tracepusher
        tracepusher_response = run_tracepusher(args)

        if DEBUG_MODE:
            print(tracepusher_response)



if DEBUG_MODE:
    print("-"*25)
    print(" > Top Level Stats < ")
    print(f"Pages in this HAR: {len(har_json['log']['pages'])}")
    print(f"page trace id: {trace_id[:7]} ({page_ref} | {page_name})") # Jaeger shows first 7 chars of trace id. Print for debugging.
    print("-"*25)
print("Done...")