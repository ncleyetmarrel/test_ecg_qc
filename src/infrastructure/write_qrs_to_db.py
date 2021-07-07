import json
from datetime import datetime, timedelta

from influxdb import InfluxDBClient

from src.domain.detect_qrs import SAMPLING_FREQUENCY as sf

DEFAULT_AMPLITUDE_VALUE = 0
INITIAL_TIMESTAMP = datetime(2021, 2, 15)

INFLUXDB_HOST = "influxdb"
INFLUXDB_USERNAME = "admin"
INFLUXDB_PASSWORD = "auraadmin"
INFLUXDB_DBNAME = "qrs"
INFLUXDB_PORT = 8086

QRS_FILE_PREFIX = 'output/frames/hamilton_mit_bih_noise_stress'


def connect_client_to_db(client: InfluxDBClient, dbname: str) -> None:
    dbs = client.get_list_database()
    if dbname not in [d['name'] for d in dbs if 'name' in d]:
        print(f"Creating database {dbname}.")
        client.create_database(dbname)
    client.switch_database(dbname)


def write_qrs_to_db(SNR: str) -> None:
    influx_client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT,
                                   username=INFLUXDB_USERNAME,
                                   password=INFLUXDB_PASSWORD)
    connect_client_to_db(influx_client, INFLUXDB_DBNAME)
    json_file = f'{QRS_FILE_PREFIX}_{SNR}.json'
    with open(json_file) as qrs_json:
        qrs_dict = json.load(qrs_json)
    qrs_json.close()
    try:
        snr_int = int(SNR[-2:])
    except ValueError:
        snr_int = -6  # case where SNR='e_6'
    points = []
    for patient in iter(qrs_dict.keys()):  # For each patient
        channel_dict = qrs_dict[patient]
        for channel in iter(channel_dict):  # For each channel
            qrs_list = channel_dict[channel]
            for qrs_frame in qrs_list:
                timestamp = str(INITIAL_TIMESTAMP +
                                timedelta(
                                    milliseconds=qrs_frame/sf*1000)
                                )
                point = {
                            'measurement': 'DetectedQRS',
                            'tags': {
                                'patient': str(patient.split('e')[0]),
                                'snr': snr_int,
                                'channel': channel
                            },
                            'time': timestamp,
                            'fields': {
                                'amplitude': DEFAULT_AMPLITUDE_VALUE
                            }
                }
                points.append(point)
    influx_client.write_points(points=points, time_precision='u')
    influx_client.close()
