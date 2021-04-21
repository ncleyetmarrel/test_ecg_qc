# Test ECG_QC

This project aims to test the performance of the package [ECG_QC](https://github.com/Aura-healthcare/ecg_qc).

## Installation/Prerequisites

First download the dependencies :
```
$ pip install -r requirements.txt
```  
Then, set up Airflow in your working directory :
```
$ export AIRFLOW_HOME=$(pwd)
$ export AIRFLOW_CONFIG=$AIRFLOW_HOME/airflow.cfg
```
Initialize airflow database and create an admin user :
```
$ airflow init db
$ airflow users create \
    --username admin \
    --firstname Firstname \
    --lastname Lastname \
    --role Admin \
    --email admin@admin.org
 ```
 You will be asked to choose a password. Then you can start the web server :
 ```
$ airflow webserver
```  
 
