from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago


# STEP 1

# Task 1 :
def extract_data():
    # TODO
    pass


# Task 2 :
def detect_qrs():
    # TODO
    pass


# Task 3 :
def compute_ratio():
    # TODO
    pass


# STEP 2

# Task 4 :
def apply_ecg_qc():
    # TODO
    pass


# Task 5 :
def write_timestamp_to_db():
    # TODO
    pass


# Task 6 :
def relaunch_task_2_3():
    # TODO
    pass


with DAG(
    'dag_python',
    description='Run python scripts to test ecg_qc',
    start_date=days_ago(2),
) as dag:

    t1 = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
    )

    t2 = PythonOperator(
        task_id='detect_qrs',
        python_callable=detect_qrs,
    )

    t1 >> t2
