from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

from tasks.tasks import apply_ecg_qc, write_timestamp_to_db,\
    relaunch_task_2_3

from tasks.extract_data import extract_data
from tasks.detect_qrs import detect_qrs
from tasks.compute_ratio import compute_ratio

# Parameters
data_path = 'data'
tolerance = 50
SNR = 'e_6'


with DAG(
    'dag_python',
    description='Run python scripts to test ecg_qc',
    start_date=datetime(2021, 4, 22),
) as dag:

    t_extract_data = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        op_kwargs={
            'data_path': data_path
        },
        dag=dag
    )

    t_detect_qrs = PythonOperator(
        task_id='detect_qrs',
        python_callable=detect_qrs,
        op_kwargs={
            'snr': SNR,
            'data_path': data_path
        },
        dag=dag
    )

    t_compute_ratio = PythonOperator(
        task_id='compute_ratio',
        python_callable=compute_ratio,
        op_kwargs={
            'snr': SNR,
            'tol': tolerance
        },
        dag=dag
    )

    t_apply_ecg_qc = PythonOperator(
        task_id='apply_ecg_qc',
        python_callable=apply_ecg_qc,
        dag=dag
    )

    t_write_timestamp_to_db = PythonOperator(
        task_id='write_timestamp_to_db',
        python_callable=write_timestamp_to_db,
        dag=dag,
    )

    t_relaunch_task_2_3 = PythonOperator(
        task_id='relaunch_task_2_3',
        python_callable=relaunch_task_2_3,
        dag=dag
    )

    t_extract_data >> t_detect_qrs >> t_compute_ratio >> t_apply_ecg_qc >> \
        t_write_timestamp_to_db >> t_relaunch_task_2_3
