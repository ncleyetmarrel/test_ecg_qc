import pandas as pd
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import connection, ISOLATION_LEVEL_AUTOCOMMIT


def get_connection_to_db(host: str = "postgres", port: int = 5432,
                         database: str = "postgres", user: str = "postgres",
                         password: str = "postgres") -> connection:
    try:
        conn = psycopg2.connect(host=host, port=port,
                                database=database, user=user,
                                password=password)
    except (Exception, Error):
        print(f"Database {database} does not exist. Creating one...")
        conn = psycopg2.connect(host=host, port=port, user=user,
                                password=password)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE {database};")
        print(f"Database {database} has been created.")
        cursor.close()
        conn.close()
        conn = psycopg2.connect(host=host, port=port,
                                database=database, user=user,
                                password=password)
    finally:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn


def write_metrics_to_db(model_ECG_QC: str, SNR: str, tol: int,
                        date_run: str, table_name: str = "metrics") -> None:
    # TODO : maybe host=os.getenv('POSTGRES_HOST_URL')
    conn = get_connection_to_db()
    cursor = conn.cursor()
    # Check if the table already exists
    cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE \
                   table_name='{table_name}';")
    if not cursor.fetchone()[0]:
        print(f"Table {table_name} does not exist. Creating one...")
        cursor.execute(f"CREATE TABLE {table_name} \
            (model_ecg_qc varchar, \
            snr integer, \
            tol integer, \
            date_run timestamp, \
            patient varchar, \
            failure_detection real, \
            positive_predictivity real, \
            sensitivity real, \
            f1_score real \
            );")
        print(f"Table {table_name} has been created")
    if model_ECG_QC != 'None':
        file_name = ("output/perf/hamilton_mit_bih_noise_stress"
                     f"_{SNR}_{model_ECG_QC}_{tol}.csv")
    else:
        file_name = ("output/perf/hamilton_mit_bih_noise_stress"
                     f"_{SNR}_{tol}.csv")
    df = pd.read_csv(file_name, index_col=0)
    # Delete blank row
    df.drop(axis=0, labels='_____', inplace=True)
    # Change format of SNR
    try:
        snr_int = int(SNR[-2:])
    except ValueError:
        snr_int = -6  # case where SNR='e_6'
    for index, row in df.iterrows():
        cursor.execute(f"INSERT INTO {table_name} VALUES \
            ('{model_ECG_QC}', \
            {snr_int}, \
            {tol}, \
            TIMESTAMP '{date_run}', \
            '{index.split('e')[0]}', \
            {row['F(%)']}, \
            {row['P+(%)']}, \
            {row['Se(%)']}, \
            {row['F1(%)']} \
            );")
    cursor.close()
    conn.close()
