import os
import json

import wfdb
import pandas as pd
import numpy as np

from typing import Generator, Dict, Tuple, List
from biosppy.signals.ecg import ecg


def read_mit_bih_noise(snr: str, data_path: str) -> \
        Generator[Tuple[str, Dict[str, np.ndarray]], None, None]:
    """
    read records with SNR from MIT BIH Noise Stress Test Database.
    :return: ID and values of sampled signals for each record
    :rtype: tuple(str, dict(str, ndarray))
    """
    assert snr in ['e24', 'e18', 'e12', 'e06', 'e00', 'e_6']
    rec_list = pd.read_csv(
        f'{data_path}/mit-bih-noise-stress-test-database/RECORDS',
        names=['id']
        )
    records_list = [record_id for record_id in rec_list['id']
                    if record_id.find(snr) != -1]
    for record_id in records_list:
        record = wfdb.rdrecord(
            f'{data_path}/mit-bih-noise-stress-test-database/{record_id}'
            )
        yield record_id, {
            record.sig_name[0]: record.p_signal[:, 0],
            record.sig_name[1]: record.p_signal[:, 1]
        }


def run_hamilton_qrs_detector(sig: np.ndarray, freq_sampling: int) -> \
        List[int]:
    qrs_detections = ecg(
        signal=sig, sampling_rate=freq_sampling, show=False
        )[2]
    return [int(element) for element in qrs_detections]


def write_detections_json(snr: str, dict_detections:
                          Dict[str, Dict[str, List[int]]]) -> None:
    """
    write results of QRS detection from a dictionary in a json file.
    :param dataset: name of the studied dataset
    :type dataset: str
    :param algorithm: name of the used method for QRS detection
    :type algorithm: str
    :param dict_detections: results of QRS detections (localisations)
     for each record and each channel
    :type dict_detections: dict(str, dict(str, list(int)))
    """
    os.makedirs('output/frames', exist_ok=True)
    with open(
        f'output/frames/hamilton_mit_bih_noise_stress_{snr}.json', 'w'
            ) as outfile:
        json.dump(dict_detections, outfile)


def detect_qrs(snr: str, data_path: str = 'data') -> None:
    assert snr in ['e24', 'e18', 'e12', 'e06', 'e00', 'e_6']
    dataset = 'mit-bih-noise-stress-test-' + snr
    data_generator = read_mit_bih_noise(snr, data_path)
    records_dict = records[dataset]
    detections_dict = {}
    counter = 0
    print(f'Detection with Hamilton on dataset {dataset} is running....')
    while True:
        try:
            record_id, record_sigs = next(data_generator)
            sig_names = records_dict[str(record_id)]
            detections_rec_dict = {}
            for id_sig in range(len(sig_names)):
                qrs_frames = run_hamilton_qrs_detector(
                    record_sigs[sig_names[id_sig]], sampling_frequency
                    )
                detections_rec_dict[sig_names[id_sig]] = qrs_frames
            detections_dict[record_id] = detections_rec_dict
            counter += 1
            print(f'{counter}/{len(records_dict.keys())}')
        except StopIteration:
            write_detections_json(snr, detections_dict)
            print(f'Detection with Hamilton on dataset {dataset} \
            was successful....')
            break


# MIT-BIH Noise Stress Database
# records and their channels
# s/o to Marie !!!

mit_bih_noise_stress_test_e24 = {
    '118e24': ['MLII', 'V1'],
    '119e24': ['MLII', 'V1']
}

mit_bih_noise_stress_test_e18 = {
    '118e18': ['MLII', 'V1'],
    '119e18': ['MLII', 'V1']
}

mit_bih_noise_stress_test_e12 = {
    '118e12': ['MLII', 'V1'],
    '119e12': ['MLII', 'V1']
}

mit_bih_noise_stress_test_e06 = {
    '118e06': ['MLII', 'V1'],
    '119e06': ['MLII', 'V1']
}

mit_bih_noise_stress_test_e00 = {
    '118e00': ['MLII', 'V1'],
    '119e00': ['MLII', 'V1']
}

mit_bih_noise_stress_test_e_6 = {
    '118e_6': ['MLII', 'V1'],
    '119e_6': ['MLII', 'V1']
}

# generator for records' readers
'''
dataset_generators = {
    'mit-bih-noise-stress-test-e24': read_mit_bih_noise('e24'),
    'mit-bih-noise-stress-test-e18': read_mit_bih_noise('e18'),
    'mit-bih-noise-stress-test-e12': read_mit_bih_noise('e12'),
    'mit-bih-noise-stress-test-e06': read_mit_bih_noise('e06'),
    'mit-bih-noise-stress-test-e00': read_mit_bih_noise('e00'),
    'mit-bih-noise-stress-test-e_6': read_mit_bih_noise('e_6'),

}
'''

# generator to get names of records and their channels
records = {
    'mit-bih-noise-stress-test-e24': mit_bih_noise_stress_test_e24,
    'mit-bih-noise-stress-test-e18': mit_bih_noise_stress_test_e18,
    'mit-bih-noise-stress-test-e12': mit_bih_noise_stress_test_e12,
    'mit-bih-noise-stress-test-e06': mit_bih_noise_stress_test_e06,
    'mit-bih-noise-stress-test-e00': mit_bih_noise_stress_test_e00,
    'mit-bih-noise-stress-test-e_6': mit_bih_noise_stress_test_e_6,
}

# signals' sampling frequency
sampling_frequency = 360
