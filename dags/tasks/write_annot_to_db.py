import json
from datetime import datetime, timedelta

from influxdb import InfluxDBClient
from dags.tasks.detect_qrs import sampling_frequency as sf

DEFAULT_AMPLITUDE_VALUE = 1
INITIAL_TIMESTAMP = datetime(2021, 2, 15)


def get_connection_to_db(host: str = "influxdb", port: int = 8086,
                         username: str = "admin", password: str = "auraadmin",
                         dbname: str = "qrs") -> InfluxDBClient:
    client = InfluxDBClient(host=host, port=port, username=username,
                            password=password)
    dbs = client.get_list_database()
    if dbname not in [d['name'] for d in dbs if 'name' in d]:
        print("Creating database.")
        client.create_database(dbname)
    client.switch_database(dbname)
    return client


def write_annot_to_db() -> None:
    client = get_connection_to_db()
    # Load QRS json
    json_file = 'output/annotations/mit_bih_noise_stress.json'
    with open(json_file) as qrs_json:
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
    client.write_points(points=points, time_precision='u')
    client.close()
