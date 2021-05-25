from datetime import datetime, timedelta

from influxdb import InfluxDBClient
from dags.tasks.detect_qrs import sampling_frequency as sf
from dags.tasks.detect_qrs import read_mit_bih_noise

INITIAL_TIMESTAMP = datetime(2021, 2, 15)
BATCH_SIZE = 10000


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


def write_ecg_to_db(SNR: str,  data_path: str = 'data') -> None:
    client = get_connection_to_db()
    data_generator = read_mit_bih_noise(SNR, data_path)
    try:
        snr_int = int(SNR[-2:])
    except ValueError:
        snr_int = -6  # case where SNR='e_6'
    points = []
    while True:
        try:
            patient, signals_dic = next(data_generator)
            for channel in iter(signals_dic.keys()):
                signal = signals_dic[channel]
                frame = 0
                for amp in signal:
                    timestamp = INITIAL_TIMESTAMP + \
                                timedelta(
                                    milliseconds=frame/sf*1000
                                )
                    # point = {
                    #         'measurement': 'ECG',
                    #         'tags': {
                    #             'patient': str(patient.split('e')[0]),
                    #             'snr': snr_int,
                    #             'channel': channel
                    #         },
                    #         'time': timestamp,
                    #         'fields': {
                    #             'amplitude': amp
                    #         }
                    # }
                    point = (f"ECG,patient={str(patient.split('e')[0])},"
                             f"snr={snr_int},channel={channel} amplitude={amp}"
                             f" {int(timestamp.timestamp()*1000)}")
                    points.append(point)
                    frame += 1
        except StopIteration:
            client.write_points(points=points, time_precision='ms',
                                batch_size=BATCH_SIZE, protocol='line')
            client.close()
            break
