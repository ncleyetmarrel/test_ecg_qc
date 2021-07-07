import json
from datetime import datetime, timedelta

from influxdb import InfluxDBClient

from src.domain.detect_qrs import SAMPLING_FREQUENCY as sf

DEFAULT_AMPLITUDE_VALUE = 1
INITIAL_TIMESTAMP = datetime(2021, 2, 15)

INFLUXDB_HOST = "influxdb"
INFLUXDB_USERNAME = "admin"
INFLUXDB_PASSWORD = "auraadmin"
INFLUXDB_DBNAME = "qrs"
INFLUXDB_PORT = 8086

ANNOTATION_FILE = 'output/annotations/mit_bih_noise_stress.json'


def connect_client_to_db(client: InfluxDBClient, dbname: str) -> None:
    dbs = client.get_list_database()
    if dbname not in [d['name'] for d in dbs if 'name' in d]:
        print(f"Creating database {dbname}.")
        client.create_database(dbname)
    client.switch_database(dbname)


def write_annot_to_db() -> None:
    influx_client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT,
                                   username=INFLUXDB_USERNAME,
                                   password=INFLUXDB_PASSWORD)
    connect_client_to_db(influx_client, INFLUXDB_DBNAME)
    with open(ANNOTATION_FILE) as qrs_json:
        qrs_dict = json.load(qrs_json)
    qrs_json.close()
    points = []
    for key in iter(qrs_dict.keys()):
        [patient, SNR] = key.split('e')
        try:
            snr_int = int(SNR[-2:])
        except ValueError:
            snr_int = -6  # case where SNR='e_6'
        signal = qrs_dict[key]
        for qrs_frame in signal:
            timestamp = str(INITIAL_TIMESTAMP +
                            timedelta(
                                milliseconds=qrs_frame/sf*1000)
                            )
            point = {
                        'measurement': 'TrueQRS',
                        'tags': {
                            'patient': patient,
                            'snr': snr_int,
                        },
                        'time': timestamp,
                        'fields': {
                            'amplitude': DEFAULT_AMPLITUDE_VALUE
                        }
            }
            points.append(point)
    influx_client.write_points(points=points, time_precision='u')
    influx_client.close()
