import os
import pandas as pd

import ecg_qc
from dags.tasks.detect_qrs import sampling_frequency as sf
from dags.tasks.detect_qrs import read_mit_bih_noise

SNR = 'e12'
data_path = 'data'

lib_path = os.path.dirname(ecg_qc.__file__)
model = 'rfc'  # or xgb
# /!\ pip not up to date (no model for specific segment len)
model_path = f"{lib_path}/ml/models/{model}.joblib"

data_generator = read_mit_bih_noise(SNR, data_path)
algo = ecg_qc.ecg_qc(sampling_frequency=sf, model=model_path)

length_chunk = 9  # seconds

patient, signals_dict = next(data_generator)
for channel in iter(signals_dict.keys()):
    signal = signals_dict[channel]
    # Preprocess signal : chunks of length_chunk seconds
    n = length_chunk * sf
    signal_subdiv = [signal[i * n:(i + 1) * n]
                     for i in range((len(signal) + n - 1) // n)]
    # Padding on last chunk
    if len(signal_subdiv[-1]) < n:
        pass
    # Apply ecg_qc on each chunk
    signal_quality = [algo.get_signal_quality(x)
                      for x in signal_subdiv[:-1]]
    try:  # last chunk might be troublesome due to its length
        last_pred = algo.get_signal_quality(signal_subdiv[-1])
        signal_quality.append(last_pred)
    except ValueError:
        print("Last chunk raised a ValueError during prediction.")

    df = pd.DataFrame(columns=["start", "end"])
    for i in range(len(signal_quality)):
        chunk_is_noisy = not signal_quality[i]
        if chunk_is_noisy:
            frame_start = n*i
            frame_end = (i+1)*n-1
            df = df.append(pd.DataFrame([[frame_start, frame_end]],
                           columns=["start", "end"]), ignore_index=True)

    # TODO: Ask question to alexis and clement to know what to store
    # Store length signal quality + length dataframe (+ % noisy segments ?) in Postgresql
    pass

    # Create (visual) annotations in grafana
    pass

    break


# 1 -> good quality / 0 -> bad quality
