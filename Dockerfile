# syntax=docker/dockerfile:1
FROM python:3.11-slim-bullseye AS python

ENV PYTHONUNBUFFERED 1
WORKDIR /marsbots

COPY src src
COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY requirements.lock requirements.txt

RUN apt-get update \
    && apt-get install -y git \
    && pip install -r requirements.txt

RUN pip install websocket-client>=1.8.0 websockets==12.0
RUN pip install git+https://github.com/edenartlab/eden2#subdirectory=sdk

ENTRYPOINT ["python", "src/run.py"]
CMD [""]
