import pytest
import subprocess

def run_tracepusher(args=""):
    output = subprocess.run(f"python3 tracepusher.py {args}" , capture_output=True, shell=True, text=True)
    return output

# Run tracepusher with no input params
# Should error and so check error is present
def test_run_no_params():
    output = run_tracepusher()
    assert output.returncode > 0
    assert output.stderr != ""
    assert "error" in output.stderr

def test_check_debug_mode():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Debug mode is ON" in output.stdout

def test_check_dry_run_mode():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Dry run mode is ON" in output.stdout

def test_check_collector_url():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Collector URL: http://otelcollector:4317" in output.stdout

def test_check_service_name():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Service Name: serviceA" in output.stdout

def test_check_span_name():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Span Name: spanOne" in output.stdout

def test_trace_length():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Trace Length (s): 2" in output.stdout

def test_check_time_shift_enabled():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --time-shift true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Time shift enabled" in output.stdout
    assert "Time shifted? True" in output.stdout
    
def test_check_time_shift_disabled():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Time shifted? False" in output.stdout

def test_span_kind_internal():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'kind': 'SPAN_KIND_INTERNAL'" in output.stdout

# Tracepusher should respect a span kind
# set to INTERNAL and leave it as such
def test_span_kind_set_to_internal():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-kind INTERNAL"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'kind': 'SPAN_KIND_INTERNAL'" in output.stdout

# Tracepusher works with
# span kind CLIENT
def test_span_kind_set_to_client():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-kind CLIENT"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'kind': 'SPAN_KIND_CLIENT'" in output.stdout

# Tracepusher works with
# span kind SERVER
def test_span_kind_set_to_server():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-kind SERVER"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'kind': 'SPAN_KIND_SERVER'" in output.stdout

# Tracepusher works with
# span kind CONSUMER
def test_span_kind_set_to_consumer():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-kind CONSUMER"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'kind': 'SPAN_KIND_CONSUMER'" in output.stdout

# Tracepusher works with
# span kind PRODUCER
def test_span_kind_set_to_producer():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-kind PRODUCER"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'kind': 'SPAN_KIND_PRODUCER'" in output.stdout

# Tracepusher should transform a
# span kind "UNSPECIFIED" to "INTERNAL"
# automatically
def test_span_kind_unspecified_to_internal():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-kind UNSPECIFIED"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'kind': 'SPAN_KIND_INTERNAL'" in output.stdout

# An error should be thrown
# If an invalid span kind is set
def test_for_invalid_span_kind():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-kind SOME-INVALID_SPAN-KIND"
    output = run_tracepusher(args)
    assert output.returncode > 0
    assert "Error: invalid span kind provided." in output.stderr

# Duration type should default to seconds
def test_for_default_duration_type():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Duration Type: s" in output.stdout

# Duration type should be milliseconds
def test_for_duration_type_milliseconds():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --duration-type ms"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "Duration Type: ms" in output.stdout

# An error should be thrown
# If an invalid duration type is set
def test_for_invalid_duration_type():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --duration-type hours"
    output = run_tracepusher(args)
    assert output.returncode > 0
    assert "Error: Duration Type invalid." in output.stderr

# Check setting parent span works
def test_for_parent_span_is_set():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --parent-span-id abc123"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "> Pushing a child (sub) span with parent span id: abc123" in output.stdout

# Check passing span events works
def test_span_events_set_correctly():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-events 0=eventA=foo=bar"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'droppedEventsCount': 0" in output.stdout

# Check passing span events works
def test_sending_multiple_span_events():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-events 0=eventA=foo=bar 100=eventB=foo=bar"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'droppedEventsCount': 0" in output.stdout
    assert "{'key': 'foo', 'value': {'stringValue': 'bar'}}" in output.stdout
    assert "{'key': 'foo', 'value': {'stringValue': 'bar'}}" in output.stdout

# Check passing an invalid
# span event is dropped
# This span event is missing a parameter
def test_drop_invalid_span_event():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-events 0=foo=bar"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'droppedEventsCount': 1" in output.stdout

# Check sending valid span attribute
def test_check_valid_span_attribute():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-attributes foo=bar"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'droppedAttributesCount': 0" in output.stdout

# Check sending valid span attribute
def test_check_intValue_span_attribute():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-attributes userID=23=intValue"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'droppedAttributesCount': 0" in output.stdout
    assert "'intValue': '23'" in output.stdout

# Check sending multiple valid span attribute
def test_check_intValue_span_attribute():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-attributes foo=bar userID=23=intValue"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'droppedAttributesCount': 0" in output.stdout
    assert "'stringValue': 'bar'" in output.stdout
    assert "'intValue': '23'" in output.stdout

# Check sending multiple valid span attribute
def test_check_one_valid_one_invalid_span_attribute():
    args = "-ep http://otelcollector:4317 -sen serviceA -spn spanOne -dur 2 --dry-run true --debug true --span-attributes foo=bar=dsd=ds userID=23=intValue"
    output = run_tracepusher(args)
    assert output.returncode == 0
    assert "'droppedAttributesCount': 1" in output.stdout
    assert "'intValue': '23'" in output.stdout