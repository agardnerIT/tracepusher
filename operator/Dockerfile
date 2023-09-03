# docker buildx build --platform linux/arm64,linux/amd64 -f Dockerfile --push -t gardnera/jobtracer-operator:dev .
# Stage 1: Copy all files into the build-env container
FROM python:3-slim AS build-env
WORKDIR /app
COPY tracepusher.py /app
COPY operator-logic.py /app
COPY requirements-operator.txt /app
RUN apk --update add gcc build-base # required to build some of the following pip packages
RUN pip install --no-cache-dir -r /app/requirements-operator.txt


# Stage 2: Use Google distroless and only copy in the app files
FROM gcr.io/distroless/python3

COPY --from=build-env /app /app
# Copy site-packages (which contains the 'requests' module from 'build-env' into the new image)
COPY --from=build-env /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
WORKDIR /app
# Make sure Python knows where to find the 'requests' module
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

CMD kopf run /app/operator-logic.py # start our operator on container creation
