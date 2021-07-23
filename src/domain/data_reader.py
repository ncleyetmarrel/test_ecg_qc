from typing import Generator, Dict, Tuple

import wfdb
import pandas as pd
import numpy as np

# MIT-BIH Noise Stress Database
# records and their channels

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

# annotations corresponding to beats so related to QRS complexes' localisations
MIT_BEAT_LABELS = ['N', 'L', 'R', 'B', 'A', 'a', 'J', 'S', 'V', 'r', 'F', 'e',
                   'j', 'n', 'E', '/', 'f', 'Q', '?']

# generator to get names of records and their channels
RECORDS = {
    'mit-bih-noise-stress-test-e24': mit_bih_noise_stress_test_e24,
    'mit-bih-noise-stress-test-e18': mit_bih_noise_stress_test_e18,
    'mit-bih-noise-stress-test-e12': mit_bih_noise_stress_test_e12,
    'mit-bih-noise-stress-test-e06': mit_bih_noise_stress_test_e06,
    'mit-bih-noise-stress-test-e00': mit_bih_noise_stress_test_e00,
    'mit-bih-noise-stress-test-e_6': mit_bih_noise_stress_test_e_6,
}

# signals' sampling frequency
SAMPLING_FREQUENCY = 360


def read_mit_bih_noise(snr: str, data_path: str) -> \
        Generator[Tuple[str, Dict[str, np.ndarray]], None, None]:
    """
    read records with SNR from MIT BIH Noise Stress Test Database.
    :return: ID and values of sampled signals for each record
    :rtype: tuple(str, dict(str, ndarray))
    """
    rec_list = pd.read_csv(
        f'{data_path}/mit-bih-noise-stress-test-database/RECORDS',
        names=['id'],
        dtype=str
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
