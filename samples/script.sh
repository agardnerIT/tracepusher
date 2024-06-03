#!/bin/bash

# Download tracepusher binary
# Do this ONCE, outside of the shell script!
# This binary shown below is for MacOS
# Change tracepusher_binary as appropriate for your environment
#   windows = tracepusher_${tracepusher_version}.exe
#   linux = tracepusher_linux_x64_${tracepusher_version}
#
# If you can't sudo, remove that line and run tracepusher
# from the local directory
# ie. change "tracepusher" to "./tracepusher" on lines 45 and 65
#
# == DOWNLOAD CODE - DO THIS ONCE ==
# tracepusher_version=0.10.0
# tracepusher_binary=tracepusher_darwin_${tracepusher_version}
# wget --quiet -O tracepusher https://github.com/agardnerIT/tracepusher/releases/download/${tracepusher_version}/${tracepusher_binary}
# chmod +x tracepusher
# sudo mv tracepusher /usr/local/bin

trace_id=$(openssl rand -hex 16)
span_id=$(openssl rand -hex 8)

echo "trace_id: ${trace_id}"
echo "span_id: ${span_id}"

main_time_start=0
echo "main time_start: ${main_time_start}"

counter=1
limit=3

while [ $counter -le $limit ]
do
  # This is unique to this span
  sub_span_id=$(openssl rand -hex 8)
  time_start=$SECONDS
  echo "loop: ${counter}"
  sleep 1
  time_end=$SECONDS
  duration=$(( $time_end - $time_start ))
  echo "loop time_start: ${time_start}. time_end: ${time_end}. duration: ${duration}"

  tracepusher \
    --endpoint=http://localhost:4318 \
    --service-name=serviceA \
    --span-name="subspan${counter}" \
    --duration=${duration} \
    --trace-id=${trace_id} \
    --parent-span-id=${span_id} \
    --span-id=${sub_span_id} \
    --time-shift=True
  echo "pushing subspan: ${sub_span_id} with span name: subspan${counter}. trace id: ${trace_id} and parent span id: ${span_id} and time shifted"

  counter=$(( $counter + 1 ))

done

time_end=$SECONDS

echo "main time_start: ${main_time_start}. time_end: ${time_end}"

echo "pushing main_trace with duration: ${time_end} and trace_id: ${trace_id} and span_id=${span_id} and time shifted"
tracepusher \
  --endpoint=http://localhost:4318 \
  --service-name=serviceA \
  --span-name="main_span" \
  --duration=${time_end} \
  --trace-id=${trace_id} \
  --span-id=${span_id} \
  --time-shift=True
