FROM ubuntu:23.10
WORKDIR /app
COPY tracepusher.py /app
RUN apt update
RUN apt install -y bsdmainutils wget curl python3-requests