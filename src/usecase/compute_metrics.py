import os
import json
from typing import List, Dict

import pandas as pd

from src.domain.data_reader import SAMPLING_FREQUENCY, RECORDS
from src.domain.metrics_computer import add_eval_global_line, get_perf_dataset

PERF_FOLDER = 'output/perf'
FRAME_FOLDER = 'output/frames'
ANN_FOLDER = 'output/annotations'


def write_delays_json(algorithm: str, dataset: str, tolerance_ms: int,
                      delays_dict: Dict[str, List[int]]) -> None:
    """
    write delays between annotations and their corresponding correct
    detections for each record of the dataset from a dictionary in a json file.
    :param algorithm: name of the used method for QRS detection
    :type algorithm: str
    :param dataset: name of the studied dataset
    :type dataset: str
    :param tolerance_ms: accepted time before and after an annotation to
     consider a detection as correct
    :type tolerance_ms: int
    :param delays_dict: values of delays between annotations and their
     corresponding correct detections for each record
    :type delays_dict: dict(str, dict(str, list(int)))
    """
    os.makedirs(PERF_FOLDER, exist_ok=True)
    file_name = f'{PERF_FOLDER}/{algorithm}_{dataset}_{tolerance_ms}'
    with open(file_name + '.json', 'w') as outfile:
        json.dump(delays_dict, outfile)


def write_perf_csv(algorithm: str, dataset: str, tolerance_ms: int,
                   perf_df: pd.DataFrame) -> None:
    """
    write criteria and scores calculated for each record and the entire
    dataset from a DataFrame with all results in a csv file.
    :param algorithm: name of the used method for QRS detection
    :type algorithm: str
    :param dataset: name of the studied dataset
    :type dataset: str
    :param tolerance_ms: accepted time before and after an annotation to
     consider a detection as correct
    :type tolerance_ms: int
    :param perf_df: results of evaluation (criteria and scores)
    :type perf_df: DataFrame
    """
    os.makedirs(PERF_FOLDER, exist_ok=True)
    file_name = f'{PERF_FOLDER}/{algorithm}_{dataset}_{tolerance_ms}'
    perf_df.to_csv(
        file_name + '.csv',
        sep=',', index=True
        )


def compute_metrics(snr: str, tol: int, model: str = 'None') -> None:
    dataset_rec = 'mit-bih-noise-stress-test-' + snr
    dataset_ann = 'mit_bih_noise_stress'
    dataset = dataset_ann + '_' + snr
    if model != 'None':
        dataset_ann = dataset_ann + '_' + model
        dataset = dataset + '_' + model
    algorithm = 'hamilton'
    fs = SAMPLING_FREQUENCY
    tol_sup1 = 25
    tol_sup2 = 50
    tolerances_fr = [int((tol * fs) / 1000), int((tol_sup1 * fs) / 1000),
                     int((tol_sup2 * fs) / 1000)]
    records_dict = RECORDS[dataset_rec]
    nb_of_records = len(records_dict.keys())

    with open(f'{FRAME_FOLDER}/{algorithm}_{dataset}.json') as detections_json:
        detections_dict = json.load(detections_json)
    with open(f'{ANN_FOLDER}/{dataset_ann}.json') as annotations_json:
        annotations_dict = json.load(annotations_json)
    perf_generator = get_perf_dataset(records_dict, detections_dict,
                                      annotations_dict, tolerances_fr[0],
                                      tolerances_fr[1], tolerances_fr[2])

    total_true_pos_tol = 0
    total_true_pos_sup1 = 0
    total_true_pos_sup2 = 0
    delays_dict_tol = {}
    delays_dict_sup1 = {}
    delays_dict_sup2 = {}
    performances_tol = pd.DataFrame(
        columns=['nbofbeats', 'FP', 'FN', 'F', 'F(%)',
                 'P+(%)', 'Se(%)', 'F1(%)']
        )
    performances_sup1 = pd.DataFrame(
        columns=['nbofbeats', 'FP', 'FN', 'F', 'F(%)',
                 'P+(%)', 'Se(%)', 'F1(%)']
                 )
    performances_sup2 = pd.DataFrame(
        columns=['nbofbeats', 'FP', 'FN', 'F', 'F(%)',
                 'P+(%)', 'Se(%)', 'F1(%)']
                 )
    counter = 0
    print(f'Evaluation of performances of Hamilton on dataset {dataset} \
          is running....')
    while True:
        try:
            id_rec, list_true_pos, list_delays, list_performance = \
                next(perf_generator)
            total_true_pos_tol += list_true_pos[0]
            total_true_pos_sup1 += list_true_pos[1]
            total_true_pos_sup2 += list_true_pos[2]
            delays_dict_tol[id_rec] = list_delays[0]
            delays_dict_sup1[id_rec] = list_delays[1]
            delays_dict_sup2[id_rec] = list_delays[2]
            performances_tol = performances_tol.append(
                list_performance[0], ignore_index=False
                )
            performances_sup1 = performances_sup1.append(
                list_performance[1], ignore_index=False
                )
            performances_sup2 = performances_sup2.append(
                list_performance[2], ignore_index=False
                )
            counter += 1
            print(f'{counter}/{nb_of_records}')
        except StopIteration:
            final_performances_tol = add_eval_global_line(
                performances_tol, nb_of_records, total_true_pos_tol
                )
            final_performances_sup1 = add_eval_global_line(
                performances_sup1, nb_of_records, total_true_pos_sup1
                )
            final_performances_sup2 = add_eval_global_line(
                performances_sup2, nb_of_records, total_true_pos_sup2
                )
            write_delays_json(algorithm, dataset, tol, delays_dict_tol)
            write_delays_json(algorithm, dataset, tol_sup1, delays_dict_sup1)
            write_delays_json(algorithm, dataset, tol_sup2, delays_dict_sup2)
            write_perf_csv(algorithm, dataset, int(tol),
                           final_performances_tol)
            write_perf_csv(algorithm, dataset, tol_sup1,
                           final_performances_sup1)
            write_perf_csv(algorithm, dataset, tol_sup2,
                           final_performances_sup2)
            print(f'Evaluation of performances of Hamilton on dataset \
                {dataset} was successful....')
            break
