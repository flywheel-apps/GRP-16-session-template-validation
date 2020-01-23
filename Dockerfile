FROM python:3.7-slim-buster

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0/
WORKDIR ${FLYWHEEL}

COPY Pipfile* src ${FLYWHEEL}/

RUN apt-get update \
    && apt-get -y install git \
    && mkdir -p $FLYWHEEL \
    && useradd --no-user-group --create-home --shell /bin/bash flywheel \
    && pip install pipenv

RUN pipenv install --deploy --ignore-pipfile
