# docker buildx build --platform linux/arm64,linux/amd64 -f Dockerfile --push -t gardnera/jobtracer-operator:dev .
# Stage 1: Copy all files into the build-env container
FROM python:3-slim AS build-env
WORKDIR /app
COPY tracepusher.py /app
COPY operator-logic.py /app
COPY requirements-operator.txt /app
RUN apk --update add gcc build-base # required to build some of the following pip packages
RUN pip install --no-cache-dir kopf kubernetes requests # install our dependencies
ADD operator-logic.py /
ADD ../tracepusher.py /
CMD kopf run -A /operator-logic.py # start our operator on container creation