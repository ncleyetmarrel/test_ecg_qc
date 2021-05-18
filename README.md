# Test ECG_QC

This project aims to test the performance of the package [ECG_QC](https://github.com/Aura-healthcare/ecg_qc).

## Prerequisites

You need to have [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/) installed on your machine. 

## Get Started

### Clone repository & download data
Clone this repository and download the [MIT-BIH Noise Stress Test Database](https://physionet.org/content/nstdb/1.0.0/). Add all the files in a *mit-bih-noise-stress-test-database* folder (which will be located in the *data* folder).

### Set up environment and launch docker-compose
You can now run these commands :

```sh
    $ source env.sh
    $ rm -rf conf/provisioning/datasources/datasources.yml
    $ envsubst < "conf/template.yml" > "conf/provisioning/datasources/datasources.yml" 
    $ docker-compose up -d
```

### UI
To interact with **Airflow** you can follow this link : <localhost:8080>

To interact with **Grafana** and visualize data you can follow this link : <localhost:3000>
 
