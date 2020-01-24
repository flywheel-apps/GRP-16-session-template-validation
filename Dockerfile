FROM python:3.7-slim-buster

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0/

RUN apt-get update \
    && apt-get -y install git \
    && mkdir -p $FLYWHEEL \
    && pip install pipenv

WORKDIR ${FLYWHEEL}
COPY Pipfile* ${FLYWHEEL}/
RUN pipenv install --deploy --ignore-pipfile

COPY run.py manifest.json ${FLYWHEEL}
COPY src ${FLYWHEEL}/src
RUN chmod +x run.py
