import os
import json
from typing import Dict, List

from src.domain.data_reader import SAMPLING_FREQUENCY, RECORDS, \
    read_mit_bih_noise
from src.domain.qrs_detector import run_hamilton_qrs_detector

OUTPUT_FOLDER_PATH = 'output/frames'
OUTPUT_FILE_PREFIX = 'output/frames/hamilton_mit_bih_noise_stress'


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
    os.makedirs(OUTPUT_FOLDER_PATH, exist_ok=True)
    with open(f'{OUTPUT_FILE_PREFIX}_{snr}.json', 'w') as outfile:
        json.dump(dict_detections, outfile)


def detect_qrs(snr: str, data_path: str = 'data') -> None:
    dataset = 'mit-bih-noise-stress-test-' + snr
    data_generator = read_mit_bih_noise(snr, data_path)
    records_dict = RECORDS[dataset]
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
                    record_sigs[sig_names[id_sig]], SAMPLING_FREQUENCY
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
