from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

from tasks.extract_data import extract_data
from tasks.detect_qrs import detect_qrs
from tasks.compute_metrics import compute_metrics
from tasks.write_metrics_to_db import write_metrics_to_db
from tasks.write_qrs_to_db import write_qrs_to_db
from tasks.write_ecg_to_db import write_ecg_to_db
from tasks.write_annot_to_db import write_annot_to_db
from tasks.apply_ecg_qc import apply_ecg_qc

# Parameters
model_ECG_QC = ['rfc', 'xgb']
data_path = 'data'
tolerance = 50
SNRs = ['e_6', 'e00', 'e06', 'e12', 'e18', 'e24']
date_run = str(datetime.now())


with DAG(
    'test_ecg_qc',
    description='Run python scripts to test ecg_qc',
    start_date=datetime(2021, 4, 22),
    schedule_interval=None,
    concurrency=12
) as dag:

    t_extract_data = PythonOperator(
                task_id='extract_data',
                python_callable=extract_data,
                op_kwargs={
                    'data_path': data_path
                },
                dag=dag
            )

    t_write_annot_to_db = PythonOperator(
            task_id='write_annot_to_db',
            python_callable=write_annot_to_db,
            dag=dag
        )

    for SNR in SNRs:

        t_detect_qrs = PythonOperator(
            task_id=f'detect_qrs_{SNR}',
            python_callable=detect_qrs,
            op_kwargs={
                'snr': SNR,
                'data_path': data_path
            },
            dag=dag
        )

        t_compute_metrics = PythonOperator(
            task_id=f'compute_metrics_{SNR}',
            python_callable=compute_metrics,
            op_kwargs={
                'snr': SNR,
                'tol': tolerance,
                'model': 'None'
            },
            dag=dag
        )

        t_write_metrics_to_db = PythonOperator(
            task_id=f'write_metrics_to_db_{SNR}',
            python_callable=write_metrics_to_db,
            op_kwargs={
                'model_ECG_QC': 'None',
                'SNR': SNR,
                'tol': tolerance,
                'date_run': date_run
            },
            dag=dag
        )

        t_write_qrs_to_db = PythonOperator(
            task_id=f'write_qrs_to_db_{SNR}',
            python_callable=write_qrs_to_db,
            op_kwargs={
                'SNR': SNR
            },
            dag=dag
        )

        t_write_ecg_to_db = PythonOperator(
            task_id=f'write_ecg_to_db_{SNR}',
            python_callable=write_ecg_to_db,
            op_kwargs={
                'SNR': SNR,
                'data_path': data_path
            },
            dag=dag
        )

        [t_extract_data, t_detect_qrs] >> t_compute_metrics >> \
            t_write_metrics_to_db
        t_detect_qrs >> t_write_qrs_to_db

        for model in model_ECG_QC:

            t_apply_ecg_qc = PythonOperator(
                task_id=f'apply_ecg_qc_{SNR}_{model}',
                python_callable=apply_ecg_qc,
                op_kwargs={
                    'SNR': SNR,
                    'model': model,
                    'data_path': data_path
                },
                dag=dag
            )

            t_compute_new_metrics = PythonOperator(
                task_id=f'compute_metrics_{SNR}_{model}',
                python_callable=compute_metrics,
                op_kwargs={
                    'snr': SNR,
                    'tol': tolerance,
                    'model': model
                },
                dag=dag
            )

            t_write_new_metrics_to_db = PythonOperator(
                task_id=f'write_metrics_to_db_{SNR}_{model}',
                python_callable=write_metrics_to_db,
                op_kwargs={
                    'model_ECG_QC': model,
                    'SNR': SNR,
                    'tol': tolerance,
                    'date_run': date_run
                },
                dag=dag
            )

            [t_detect_qrs, t_extract_data] >> t_apply_ecg_qc >> \
                t_compute_new_metrics >> t_write_new_metrics_to_db

    t_extract_data >> t_write_annot_to_db
