FROM python:slim-bullseye

COPY requirements.txt ./
COPY tracepusher.py ./
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "./tracepusher.py"]