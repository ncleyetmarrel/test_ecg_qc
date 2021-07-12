import numpy as np
from typing import List

from biosppy.signals.ecg import ecg


def run_hamilton_qrs_detector(sig: np.ndarray, freq_sampling: int) -> \
        List[int]:
    qrs_detections = ecg(
        signal=sig, sampling_rate=freq_sampling, show=False
        )[2]
    return [int(element) for element in qrs_detections]
