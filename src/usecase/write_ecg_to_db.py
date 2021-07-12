from datetime import datetime, timedelta

from influxdb import InfluxDBClient

from src.domain.data_reader import SAMPLING_FREQUENCY as sf
from src.domain.data_reader import read_mit_bih_noise
from src.infrastructure.influxdb_client import connect_client_to_db

INITIAL_TIMESTAMP = datetime(2021, 2, 15)
BATCH_SIZE = 10000

INFLUXDB_HOST = "influxdb"
INFLUXDB_USERNAME = "admin"
INFLUXDB_PASSWORD = "auraadmin"
INFLUXDB_DBNAME = "qrs"
INFLUXDB_PORT = 8086


def write_ecg_to_db(SNR: str,  data_path: str = 'data') -> None:
    influx_client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT,
                                   username=INFLUXDB_USERNAME,
                                   password=INFLUXDB_PASSWORD)
    connect_client_to_db(influx_client, INFLUXDB_DBNAME)
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

                    point = (f"ECG,patient={str(patient.split('e')[0])},"
                             f"snr={snr_int},channel={channel} amplitude={amp}"
                             f" {int(timestamp.timestamp()*1000)}")
                    points.append(point)
                    frame += 1
        except StopIteration:
            influx_client.write_points(points=points, time_precision='ms',
                                       batch_size=BATCH_SIZE, protocol='line')
            influx_client.close()
            break
