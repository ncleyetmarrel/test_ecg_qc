import os
import json
import glob

from dags.tools.grafana_client import GrafanaClient
from dags.tasks.write_metrics_to_db import get_connection_to_db


def delete_model(model: str) -> None:
    key = json.loads(os.getenv('API_KEY_GRAFANA'))['key']
    client = GrafanaClient("http://grafana:3000", key)
    # Delete annotations
    client.delete_annotation_filtered_by([model])

    conn = get_connection_to_db()
    cursor = conn.cursor()
    # Delete metrics and noisy segments
    cursor.execute(f"DELETE FROM metrics WHERE model_ecg_qc='{model}';")
    cursor.execute(f"DELETE FROM noisy_info WHERE model_ecg_qc='{model}';")
    cursor.close()
    conn.close()

    # Delete output files
    files = glob.glob(f'output/**/*_{model}*', recursive=True)
    for f in files:
        os.remove(f)
