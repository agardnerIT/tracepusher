# Run build command from root directory
# docker buildx build --platform linux/arm64,linux/amd64 -f Dockerfile --push -t gardnera/tracepusher/operator-v0.1.0 -f operator/Dockerfile .

FROM python:3.11-alpine
COPY operator/requirements-operator.txt /
COPY operator/operator-logic.py /
COPY tracepusher.py /
RUN apk --update add gcc build-base # required to build some of the following pip packages
RUN pip install -r /requirements-operator.txt # install our dependencies
CMD kopf run -A operator-logic.py # start our operator on container creation