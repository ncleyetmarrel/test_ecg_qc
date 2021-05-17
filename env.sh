# InfluxDB env vars
export INFLUXDB_USERNAME=admin
export INFLUXDB_PASSWORD=auraadmin
export INFLUXDB_DATABASE=hackathon

# Grafana env vars
export GRAFANA_USERNAME=admin
export GRAFANA_PASSWORD=admin

# PostgreSQL env vars
export POSTGRES_HOST_URL=$(hostname -I | cut -d ' ' -f 1)
export POSTGRES_DATABASE=postgres
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# Airflow env vars
export AIRFLOW_HOME=$(pwd)
export AIRFLOW_CONFIG=$AIRFLOW_HOME/airflow.cfg
export PYTHONPATH=$(pwd)