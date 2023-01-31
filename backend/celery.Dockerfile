FROM python:3.11.0-slim

WORKDIR /backend

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc libpq-dev \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
COPY ./celery_requirements.txt /backend/celery_requirements.txt
RUN pip install -r celery_requirements.txt

COPY . /backend

