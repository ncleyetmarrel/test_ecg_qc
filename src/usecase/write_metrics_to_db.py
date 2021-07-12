import pandas as pd

from src.infrastructure.postgres_client import PostgresClient

POSTGRES_DATABASE = "postgres"

OUTPUT_FILE_PREFIX = "output/perf/hamilton_mit_bih_noise_stress"

ENTRY_NAME_TYPE_DICT = {
    "model_ecg_qc": "varchar",
    "snr": "integer",
    "tol": "integer",
    "patient": "varchar",
    "failure_detection": "real",
    "positive_predictivity": "real",
    "sensitivity": "real",
    "f1_score": "real"
}


def write_metrics_to_db(model_ECG_QC: str, SNR: str, tol: int,
                        table_name: str = "metrics") -> None:

    postgres_client = PostgresClient()
    table_exists = postgres_client.check_if_table_exists(POSTGRES_DATABASE,
                                                         table_name)
    if not table_exists:
        postgres_client.create_table(POSTGRES_DATABASE, table_name,
                                     ENTRY_NAME_TYPE_DICT)

    if model_ECG_QC != 'None':
        file_name = (f"{OUTPUT_FILE_PREFIX}_{SNR}_{model_ECG_QC}_{tol}.csv")
    else:
        file_name = (f"{OUTPUT_FILE_PREFIX}_{SNR}_{tol}.csv")
    df = pd.read_csv(file_name, index_col=0)
    df.drop(axis=0, labels='_____', inplace=True)
    try:
        snr_int = int(SNR[-2:])
    except ValueError:
        snr_int = -6  # case where SNR='e_6'
    for index, row in df.iterrows():
        values_to_insert = [f"'{model_ECG_QC}'", str(snr_int), str(tol),
                            f"'{index.split('e')[0]}'", str(row['F(%)']),
                            str(row['P+(%)']), str(row['Se(%)']),
                            str(row['F1(%)'])
                            ]
        dict_to_insert = dict(zip(ENTRY_NAME_TYPE_DICT.keys(),
                                  values_to_insert))
        postgres_client.write_in_table(POSTGRES_DATABASE, table_name,
                                       dict_to_insert)
