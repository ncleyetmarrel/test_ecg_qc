import os
import json
from datetime import datetime, timedelta

import pandas as pd
import ecg_qc

from src.domain.detect_qrs import SAMPLING_FREQUENCY as sf
from src.domain.detect_qrs import read_mit_bih_noise
from src.infrastructure.grafana_client import GrafanaClient
from src.infrastructure.postgres_client import PostgresClient

INITIAL_TIMESTAMP = datetime(2021, 2, 15)

GRAFANA_URL = "http://grafana:3000"
GRAFANA_API_KEY_ENV_VAR = 'API_KEY_GRAFANA'

DASHBOARD_NAME = "ECG QC performances"
PANEL_NAME = "ECG + Detected QRS (Hamilton)"

ANNOTATION_FILE_PREFIX = "output/annotations/mit_bih_noise_stress"
FRAME_FILE_PREFIX = "output/frames/hamilton_mit_bih_noise_stress"

POSTGRES_DATABASE = "postgres"

ENTRY_NAME_TYPE_DICT = {
    "model_ecg_qc": "varchar",
    "snr": "integer",
    "patient": "varchar",
    "chan": "varchar",
    "nb_chunks": "integer",
    "nb_noisy_chunks": "integer",
    "noisy_pourcent": "real"
}


def not_in_noisy_segment(frame: int, noisy_segments: pd.DataFrame) -> bool:
    timestamp = INITIAL_TIMESTAMP + timedelta(milliseconds=frame/sf*1000)
    timestamp = int(timestamp.timestamp()*1000)
    frame_not_in_noisy_segment = \
        len(noisy_segments[(timestamp >= noisy_segments['start']) &
            (noisy_segments['end'] >= timestamp)]) == 0
    return frame_not_in_noisy_segment


def update_noise_free_files(SNR: str, model: str, patient: str,
                            noise: pd.DataFrame) -> None:
    with open(f"{ANNOTATION_FILE_PREFIX}.json") as ann_file:
        ann_dict = json.load(ann_file)
    ann_file.close()
    ann_list = ann_dict[patient]

    with open(f"{FRAME_FILE_PREFIX}_{SNR}.json") as \
            frames_file:
        frames_dict = json.load(frames_file)
    frames_file.close()
    frames_list = frames_dict[patient]['MLII']

    ann_list = [ann for ann in ann_list if not_in_noisy_segment(ann, noise)]
    frames_list = [f for f in frames_list if not_in_noisy_segment(f, noise)]

    try:
        with open(f"{ANNOTATION_FILE_PREFIX}_{model}.json",
                  'r+') as ann_outfile:
            ann_out_dict = json.load(ann_outfile)
            ann_out_dict[patient] = ann_list
            ann_outfile.seek(0)
            json.dump(ann_out_dict, ann_outfile)
    except FileNotFoundError:
        with open(f"{ANNOTATION_FILE_PREFIX}_{model}.json",
                  'w') as ann_outfile:
            json.dump({patient: ann_list}, ann_outfile)
    ann_outfile.close()

    try:
        with open((f"{FRAME_FILE_PREFIX}_{SNR}_{model}.json"), 'r+') \
                as f_outfile:
            f_out_dict = json.load(f_outfile)
            f_out_dict[patient] = {'MLII': frames_list}
            f_outfile.seek(0)
            json.dump(f_out_dict, f_outfile)
    except FileNotFoundError:
        with open((f"{FRAME_FILE_PREFIX}_{SNR}_{model}.json"), 'w') \
                as f_outfile:
            json.dump({patient: {'MLII': frames_list}}, f_outfile)
    f_outfile.close()


def apply_ecg_qc(SNR: str, model: str, data_path: str,
                 table_name: str = "noisy_info") -> None:
    # TODO : faire otchoz
    if model != 'rfc' and model != 'xgb':
        model_path = f'models/{model}.pkl'
    else:
        model_path = f"models/{model}.joblib"

    data_generator = read_mit_bih_noise(SNR, data_path)
    algo = ecg_qc.ecg_qc(sampling_frequency=sf, model=model_path)
    length_chunk = 9  # seconds TODO parse model
    # length_chunk = int(model.split('_')[-1][:-1])

    key = json.loads(os.getenv(GRAFANA_API_KEY_ENV_VAR))['key']
    grafana_client = GrafanaClient(GRAFANA_URL, key)
    postgres_client = PostgresClient()
    table_exists = postgres_client.check_if_table_exists(POSTGRES_DATABASE,
                                                         table_name)
    if not table_exists:
        postgres_client.create_table(POSTGRES_DATABASE, table_name,
                                     ENTRY_NAME_TYPE_DICT)

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
                grafana_client.annotate_from_dataframe(DASHBOARD_NAME,
                                                       PANEL_NAME,
                                                       df)

                nb_noisy_chunks = df.shape[0]
                noisy_pourcent = round(nb_noisy_chunks/nb_chunks*100, 2)

                # Store info in Postgresql
                values_to_insert = [f"'{model}'", str(snr_int), f"'{pat}'",
                                    f"'{channel}'", str(nb_chunks),
                                    str(nb_noisy_chunks), str(noisy_pourcent)]
                dict_to_insert = dict(zip(ENTRY_NAME_TYPE_DICT.keys(),
                                          values_to_insert))
                postgres_client.write_in_table(POSTGRES_DATABASE, table_name,
                                               dict_to_insert)

                # Create / update new log files (MLII only)
                if channel == 'MLII':
                    update_noise_free_files(SNR, model, patient, df)
                    noisy_pourcent_mlii.append(noisy_pourcent)

        except StopIteration:
            # Add the global noisy pourcent in the table
            noisy_pourcent_global = \
                sum(noisy_pourcent_mlii)/len(noisy_pourcent_mlii)
            values_to_insert = [f"'{model}'", str(snr_int), "'global'",
                                "'MLII'", "NULL", "NULL",
                                str(noisy_pourcent_global)]
            dict_to_insert = dict(zip(ENTRY_NAME_TYPE_DICT.keys(),
                                      values_to_insert))
            postgres_client.write_in_table(POSTGRES_DATABASE, table_name,
                                           dict_to_insert)
            break

    # 1 -> good quality / 0 -> bad quality
