# Test ECG_QC

This project aims to test the performance of the package [ECG_QC](https://github.com/Aura-healthcare/ecg_qc) on the [MIT-BIH Noise Stress Test Database](https://physionet.org/content/nstdb/1.0.0/).

## Prerequisites

You need to have [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/) installed on your machine. 

## Get Started

### Set up environment and launch docker-compose
After cloning this repository, you can run these commands :

```sh
    $ source setup_env.sh
    $ docker-compose up -d
```

### UI
You can interact with **Airflow** [here](http://localhost:8080), and with **Grafana** [here](http://localhost:3000). Usernames and passwords are *admin* for both.

### Troubleshoot
If docker-compose returns an error due to port already in use, change the value of environment variables in the env.sh file.
