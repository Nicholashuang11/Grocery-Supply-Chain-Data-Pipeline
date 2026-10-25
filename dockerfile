FROM apache/airflow:3.3.0

USER root

RUN apt-get update && apt-get install -y --no-install-recommends default-jre-headless procps &&  apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt
