import json
from datetime import datetime, timedelta

from influxdb import InfluxDBClient
from dags.tasks.detect_qrs import sampling_frequency as sf

DEFAULT_AMPLITUDE_VALUE = 100
INITIAL_TIMESTAMP = datetime(2021, 2, 15)


def get_connection_to_db(host: str = "influxdb", port: int = 8086,
                         username: str = "admin", password: str = "auraadmin",
                         dbname: str = "qrs") -> InfluxDBClient:
    client = InfluxDBClient(host=host, port=port, username=username,
                            password=password)
    # print("Dropping database.")
    # client.drop_database(dbname)  # TODO : for tests
    dbs = client.get_list_database()
    if dbname not in [d['name'] for d in dbs if 'name' in d]:
        print("Creating database.")
        client.create_database(dbname)  # TODO : maybe drop db
    client.switch_database(dbname)
    return client


def write_qrs_to_db(SNR: str) -> None:
    client = get_connection_to_db()
    # Load QRS json
    json_file = f'output/frames/hamilton_mit_bih_noise_stress_{SNR}.json'
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
                                )  # TODO : milliseconds in chronograf ??
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
    client.write_points(points=points, time_precision='u')
    client.close()
