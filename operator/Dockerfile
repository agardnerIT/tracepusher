FROM python:3.11-alpine
RUN apk --update add gcc build-base # required to build some of the following pip packages
RUN pip install --no-cache-dir kopf kubernetes requests # install our dependencies
ADD operator-logic.py /
ADD tracepusher.py /
CMD kopf run /operator-logic.py # start our operator on container creation
