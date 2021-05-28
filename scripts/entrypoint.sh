#!/usr/bin/env bash
export PYTHONPATH=$(pwd)
airflow db init
airflow users create -r Admin -u admin -e admin@example.com -f admin -l user -p admin
airflow webserver &
airflow scheduler