import os
from airflow import DAG
from airflow.operators.python import PythonOperator
# from airflow.operators.bash import BashOperator
# from airflow.utils.dates import days_ago
from datetime import datetime

from tasks.tasks import apply_ecg_qc, write_timestamp_to_db,\
    relaunch_task_2_3

from tasks.extract_data import extract_data
from tasks.detect_qrs import detect_qrs
from tasks.compute_ratio import compute_ratio


with DAG(
    'dag_python',
    description='Run python scripts to test ecg_qc',
    start_date=datetime(2021, 4, 22),
) as dag:

    t1 = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        op_kwargs={
            'data_path': os.getenv('AIRFLOW_HOME') + '/data'
        },
        dag=dag
    )

    t2 = PythonOperator(
        task_id='detect_qrs',
        python_callable=detect_qrs,
        op_kwargs={
            'snr': 'e_6',
            'data_path': os.getenv('AIRFLOW_HOME') + '/data'
        },
        dag=dag
    )

    t3 = PythonOperator(
        task_id='compute_ratio',
        python_callable=compute_ratio,
        op_kwargs={
            'snr': 'e_6',
            'tol': 50
        },
        dag=dag
    )

    t4 = PythonOperator(
        task_id='apply_ecg_qc',
        python_callable=apply_ecg_qc,
        dag=dag
    )

    t5 = PythonOperator(
        task_id='write_timestamp_to_db',
        python_callable=write_timestamp_to_db,
        dag=dag,
    )

    t6 = PythonOperator(
        task_id='relaunch_task_2_3',
        python_callable=relaunch_task_2_3,
        dag=dag
    )

    t1 >> t2 >> t3 >> t4 >> t5 >> t6
