import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List

from psycopg2.extensions import cursor
import ecg_qc
from dags.tasks.detect_qrs import sampling_frequency as sf
from dags.tasks.detect_qrs import read_mit_bih_noise
from dags.tools.grafana_client import GrafanaClient
from dags.tasks.write_metrics_to_db import get_connection_to_db

INITIAL_TIMESTAMP = datetime(2021, 2, 15)

lib_path = os.path.dirname(ecg_qc.__file__)

# model = 'rfc'  # or xgb
# /!\ pip not up to date (no model for specific segment len)


def create_noisy_info_table(cursor: cursor):
    # Check if the table already exists
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE \
                   table_name='noisy_info';")
    if not cursor.fetchone()[0]:
        print("Table noisy_info does not exist. Creating one...")
        cursor.execute("CREATE TABLE noisy_info \
            (model_ecg_qc varchar, \
            snr integer, \
            patient varchar, \
            chan varchar, \
            nb_chunks integer, \
            nb_noisy_chunks integer, \
            noisy_pourcent real \
            );")
        print("Table noisy_info has been created")


def filter_list(liste: List, df: pd.DataFrame) -> List:
    new_list = []
    for elt in liste:
        # Convert frame into timestamp
        timestamp = INITIAL_TIMESTAMP + timedelta(milliseconds=elt/sf*1000)
        timestamp = int(timestamp.timestamp()*1000)
        if len(df[(timestamp >= df['start']) & (df['end'] >= timestamp)]) == 0:
            new_list.append(elt)
    return new_list


def update_noise_free_files(SNR: str, model: str, patient: str,
                            noise: pd.DataFrame) -> None:
    with open("output/annotations/mit_bih_noise_stress.json") as ann_file:
        ann_dict = json.load(ann_file)
    ann_file.close()
    ann_list = ann_dict[patient]

    with open(f"output/frames/hamilton_mit_bih_noise_stress_{SNR}.json") as \
            frames_file:
        frames_dict = json.load(frames_file)
    frames_file.close()
    frames_list = frames_dict[patient]['MLII']

    ann_list = filter_list(ann_list, noise)
    frames_list = filter_list(frames_list, noise)

    try:
        with open(f"output/annotations/mit_bih_noise_stress_{model}.json",
                  'r+') as ann_outfile:
            ann_out_dict = json.load(ann_outfile)
            ann_out_dict[patient] = ann_list
            ann_outfile.seek(0)
            json.dump(ann_out_dict, ann_outfile)
    except FileNotFoundError:
        with open(f"output/annotations/mit_bih_noise_stress_{model}.json",
                  'w') as ann_outfile:
            json.dump({patient: ann_list}, ann_outfile)
    ann_outfile.close()

    try:
        with open(("output/frames/hamilton_mit_bih_noise_stress"
                   f"_{SNR}_{model}.json"), 'r+') as f_outfile:
            f_out_dict = json.load(f_outfile)
            f_out_dict[patient] = {'MLII': frames_list}
            f_outfile.seek(0)
            json.dump(f_out_dict, f_outfile)
    except FileNotFoundError:
        with open(("output/frames/hamilton_mit_bih_noise_stress"
                   f"_{SNR}_{model}.json"), 'w') as f_outfile:
            json.dump({patient: {'MLII': frames_list}}, f_outfile)
    f_outfile.close()


def apply_ecg_qc(SNR: str, model: str, data_path: str) -> None:
    model_path = f"{lib_path}/ml/models/{model}.joblib"
    data_generator = read_mit_bih_noise(SNR, data_path)
    algo = ecg_qc.ecg_qc(sampling_frequency=sf, model=model_path)
    length_chunk = 9  # seconds TODO parse model
    key = json.loads(os.getenv('API_KEY_GRAFANA'))['key']
    client = GrafanaClient("http://grafana:3000", key)
    conn = get_connection_to_db()
    cursor = conn.cursor()
    create_noisy_info_table(cursor=cursor)

    try:
        snr_int = int(SNR[-2:])
    except ValueError:
        snr_int = -6  # case where SNR='e_6'

    noisy_pourcent_mlii = []
    while True:
        try:
            patient, signals_dict = next(data_generator)
            for channel in iter(signals_dict.keys()):
                signal = signals_dict[channel].tolist()
                # Preprocess signal : chunks of length_chunk seconds
                n = length_chunk * sf
                signal_subdiv = [signal[i * n:(i + 1) * n]
                                 for i in range((len(signal) + n - 1) // n)]
                # Padding on last chunk if necessary
                m = len(signal_subdiv[-1])
                if m < n:
                    signal_subdiv[-1] += [0 for j in range(n - m)]
                # Apply ecg_qc on each chunk
                signal_quality = [algo.get_signal_quality(x)
                                  for x in signal_subdiv]

                df = pd.DataFrame(columns=["start", "end", "text", "tags"])
                nb_chunks = len(signal_quality)
                for i in range(nb_chunks):
                    chunk_is_noisy = not signal_quality[i]
                    if chunk_is_noisy:
                        frame_start = n*i
                        frame_end = min(len(signal)-1, (i+1)*n-1)
                        time_start = INITIAL_TIMESTAMP + \
                            timedelta(milliseconds=frame_start/sf*1000)
                        time_start = int(time_start.timestamp()*1000)
                        time_end = INITIAL_TIMESTAMP + \
                            timedelta(milliseconds=frame_end/sf*1000)
                        time_end = int(time_end.timestamp()*1000)
                        pat = patient.split('e')[0]
                        df = df.append(
                            pd.DataFrame([[time_start, time_end,
                                          "Noisy segment",
                                           [str(snr_int), pat, channel, model]
                                           ]],
                                         columns=["start", "end", "text",
                                                  "tags"]),
                            ignore_index=True)
                client.annotate_from_dataframe("ECG QC performances",
                                               "ECG + Detected QRS (Hamilton)",
                                               df)

                nb_noisy_chunks = df.shape[0]
                noisy_pourcent = round(nb_noisy_chunks/nb_chunks*100, 2)

                # Store info in Postgresql
                cursor.execute(f"INSERT INTO noisy_info VALUES \
                               ('{model}', \
                               {snr_int}, \
                               '{pat}', \
                               '{channel}', \
                               {nb_chunks}, \
                               {nb_noisy_chunks}, \
                               {noisy_pourcent} \
                               );")

                # Create / update new log files (MLII only)
                if channel == 'MLII':
                    update_noise_free_files(SNR, model, patient, df)
                    noisy_pourcent_mlii.append(noisy_pourcent)

        except StopIteration:
            # Add the global noisy pourcent in the table
            noisy_pourcent_global = \
                sum(noisy_pourcent_mlii)/len(noisy_pourcent_mlii)
            cursor.execute(f"INSERT INTO noisy_info VALUES \
                           ('{model}', \
                           {snr_int}, \
                           'global', \
                           'MLII', \
                           NULL, \
                           NULL, \
                           {noisy_pourcent_global} \
                           );")
            cursor.close()
            conn.close()
            break

    # 1 -> good quality / 0 -> bad quality
