import json
import os
import wfdb
import pandas as pd
from typing import List, Generator, Tuple, Dict


# annotations corresponding to beats so related to QRS complexes' localisations
mit_beat_labels = ['N', 'L', 'R', 'B', 'A', 'a', 'J', 'S', 'V', 'r', 'F', 'e',
                   'j', 'n', 'E', '/', 'f', 'Q', '?']


def get_annotations_mit_bih_noise(data_path: str) -> \
        Generator[Tuple[str, List[int]], None, None]:
    """
    read annotations of records from MIT BIH Noise Stress Test Database
    and select those related to beat information.
    :return: ID and localisations of QRS complexes for each record
    :rtype: tuple(str, dict(str, ndarray))
    """
    records_list = pd.read_csv(
        f'{data_path}/mit-bih-noise-stress-test-database/RECORDS', names=['id']
        )
    for record_id in records_list['id'][:-3]:
        annotation = wfdb.rdann(
            f'{data_path}/mit-bih-noise-stress-test-database/{record_id}',
            'atr'
            )
        annot_serie = pd.Series(annotation.symbol, index=annotation.sample,
                                name="annotations")
        qrs_annotations = \
            annot_serie.iloc[:].loc[annot_serie.isin(mit_beat_labels)]
        frames_annotations_list = qrs_annotations.index.tolist()
        yield record_id, frames_annotations_list


def write_annotations_json(dict_annotations: Dict[str, List[int]]) -> None:
    """
    write localisations of beat annotations from a dictionary in a json file.
    :param dataset: name of the studied dataset
    :type dataset: str
    :param dict_annotations: localisations of beat annotations for each record
     of the dataset
    :type dict_annotations: dict(str, list(int)
    """
    os.makedirs('output/annotations', exist_ok=True)
    with open('output/annotations/mit_bih_noise_stress.json', 'w') \
            as outfile:
        json.dump(dict_annotations, outfile)


def extract_data(data_path: str = '/data') -> None:
    data_generator = get_annotations_mit_bih_noise(data_path)
    annotations_dict = {}
    print('Beat annotations on dataset mit-bih-noise-stress-test are being \
          recovered....')
    while True:
        try:
            record_id, record_annotations = next(data_generator)
            annotations_dict[record_id] = record_annotations
        except StopIteration:
            write_annotations_json(annotations_dict)
            print('Beat annotations on dataset mit-bih-noise-stress-test \
                  are successfully recovered....')
            break
