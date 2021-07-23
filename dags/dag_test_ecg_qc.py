from datetime import datetime
from os import listdir
from os.path import isfile, join

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.usecase.extract_data import extract_data
from src.usecase.detect_qrs import detect_qrs
from src.usecase.compute_metrics import compute_metrics
from src.usecase.apply_ecg_qc import apply_ecg_qc
from src.usecase.write_metrics_to_db import write_metrics_to_db
from src.usecase.write_qrs_to_db import write_qrs_to_db
from src.usecase.write_ecg_to_db import write_ecg_to_db
from src.usecase.write_annot_to_db import write_annot_to_db
from src.usecase.delete_model import delete_model
from src.infrastructure.postgres_client import PostgresClient

POSTGRES_DB = 'postgres'
METRICS_TABLE = 'metrics'
MODEL_COLUMN_NAME = 'model_ecg_qc'
SNR_COLUMN_NAME = 'snr'

START_DATE = datetime(2021, 4, 22)
CONCURRENCY = 12
SCHEDULE_INTERVAL = None

DATA_PATH = 'data'
TOLERANCE = 50
SNRs = ['e_6', 'e00', 'e06', 'e12', 'e18', 'e24']
MODEL_FOLDER = 'models'
DELETE_FOLDER = 'to_delete'


model_ECG_QC = [f for f in listdir(MODEL_FOLDER)
                if isfile(join(MODEL_FOLDER, f))]
model_to_delete = [f.split('.')[0]
                   for f in listdir(join(MODEL_FOLDER, DELETE_FOLDER))]

postgres_client = PostgresClient()

with DAG(
    'init',
    description='Initialize databases and compute metrics without model',
    start_date=START_DATE,
    schedule_interval=SCHEDULE_INTERVAL,
    concurrency=CONCURRENCY
) as dag_init:

    t_extract_data = PythonOperator(
                task_id='extract_data',
                python_callable=extract_data,
                op_kwargs={
                    'data_path': DATA_PATH
                }
            )

    t_write_annot_to_db = PythonOperator(
            task_id='write_annot_to_db',
            python_callable=write_annot_to_db
        )

    for SNR in SNRs:

        t_detect_qrs = PythonOperator(
            task_id=f'detect_qrs_{SNR}',
            python_callable=detect_qrs,
            op_kwargs={
                'snr': SNR,
                'data_path': DATA_PATH
            }
        )

        t_compute_metrics = PythonOperator(
            task_id=f'compute_metrics_{SNR}',
            python_callable=compute_metrics,
            op_kwargs={
                'snr': SNR,
                'tol': TOLERANCE,
                'model': 'None'
            }
        )

        t_write_metrics_to_db = PythonOperator(
            task_id=f'write_metrics_to_db_{SNR}',
            python_callable=write_metrics_to_db,
            op_kwargs={
                'model_ECG_QC': 'None',
                'SNR': SNR,
                'tol': TOLERANCE
            }
        )

        t_write_qrs_to_db = PythonOperator(
            task_id=f'write_qrs_to_db_{SNR}',
            python_callable=write_qrs_to_db,
            op_kwargs={
                'SNR': SNR
            }
        )

        t_write_ecg_to_db = PythonOperator(
            task_id=f'write_ecg_to_db_{SNR}',
            python_callable=write_ecg_to_db,
            op_kwargs={
                'SNR': SNR,
                'data_path': DATA_PATH
            }
        )

        [t_extract_data, t_detect_qrs] >> t_compute_metrics >> \
            t_write_metrics_to_db
        t_detect_qrs >> t_write_qrs_to_db

    t_extract_data >> t_write_annot_to_db

with DAG(
    'test_models_ecg_qc',
    description='Test ECG QC models',
    start_date=START_DATE,
    schedule_interval=SCHEDULE_INTERVAL,
    concurrency=CONCURRENCY
) as dag_test:

    for model in model_ECG_QC:

        model_name = model.split('.')[0]

        for SNR in SNRs:

            try:
                snr_int = int(SNR[-2:])
            except ValueError:
                snr_int = -6

            values_dict = {
                MODEL_COLUMN_NAME: f"'{model_name}'",
                SNR_COLUMN_NAME: str(snr_int)
            }

            if postgres_client.check_if_table_exists(
                POSTGRES_DB, METRICS_TABLE) and not \
                postgres_client.check_if_values_in_table(
                    POSTGRES_DB, METRICS_TABLE, values_dict):

                t_apply_ecg_qc = PythonOperator(
                    task_id=f'apply_ecg_qc_{SNR}_{model_name}',
                    python_callable=apply_ecg_qc,
                    op_kwargs={
                        'SNR': SNR,
                        'model': model,
                        'data_path': DATA_PATH
                    },
                )

                t_compute_new_metrics = PythonOperator(
                    task_id=f'compute_metrics_{SNR}_{model_name}',
                    python_callable=compute_metrics,
                    op_kwargs={
                        'snr': SNR,
                        'tol': TOLERANCE,
                        'model': model_name
                    }
                )

                t_write_new_metrics_to_db = PythonOperator(
                    task_id=f'write_metrics_to_db_{SNR}_{model_name}',
                    python_callable=write_metrics_to_db,
                    op_kwargs={
                        'model_ECG_QC': model_name,
                        'SNR': SNR,
                        'tol': TOLERANCE,
                    }
                )

                t_apply_ecg_qc >> t_compute_new_metrics >> \
                    t_write_new_metrics_to_db


with DAG(
    'delete_models',
    description='Delete ECG QC models from databases',
    start_date=START_DATE,
    schedule_interval=SCHEDULE_INTERVAL,
    concurrency=CONCURRENCY
) as dag_delete:

    if postgres_client.check_if_table_exists(
            POSTGRES_DB, METRICS_TABLE):

        for model in model_to_delete:
            t_delete_model = PythonOperator(
                task_id=f'delete_{model}',
                python_callable=delete_model,
                op_kwargs={
                    'model': model
                }
            )
