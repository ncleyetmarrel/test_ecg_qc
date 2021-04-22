from airflow import DAG
from airflow.operators.python import PythonOperator
# from airflow.utils.dates import days_ago
from datetime import datetime

from src.tasks import extract_data, detect_qrs, compute_ratio, \
    apply_ecg_qc, write_timestamp_to_db, relaunch_task_2_3


with DAG(
    'dag_python',
    description='Run python scripts to test ecg_qc',
    start_date=datetime(2021, 4, 22),
) as dag:

    t1 = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
    )

    t2 = PythonOperator(
        task_id='detect_qrs',
        python_callable=detect_qrs,
    )

    t3 = PythonOperator(
        task_id='compute_ratio',
        python_callable=compute_ratio,
    )

    t4 = PythonOperator(
        task_id='apply_ecg_qc',
        python_callable=apply_ecg_qc,
    )

    t5 = PythonOperator(
        task_id='write_timestamp_to_db',
        python_callable=write_timestamp_to_db,
    )

    t6 = PythonOperator(
        task_id='relaunch_task_2_3',
        python_callable=relaunch_task_2_3,
    )

    t1 >> t2 >> t3 >> t4 >> t5 >> t6
