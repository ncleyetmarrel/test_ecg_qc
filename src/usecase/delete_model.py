import os
import json
import glob

from src.infrastructure.grafana_client import GrafanaClient
from src.infrastructure.postgres_client import PostgresClient

GRAFANA_URL = "http://grafana:3000"
GRAFANA_API_KEY_ENV_VAR = 'API_KEY_GRAFANA'

POSTGRES_DATABASE = "postgres"


def delete_model(model: str) -> None:
    key = json.loads(os.getenv(GRAFANA_API_KEY_ENV_VAR))['key']
    grafana_client = GrafanaClient(GRAFANA_URL, key)
    grafana_client.delete_annotation_filtered_by([model])

    postgres_client = PostgresClient()
    dict_to_delete = {"model_ecg_qc": f"'{model}'"}
    postgres_client.delete_from_table(POSTGRES_DATABASE, "metrics",
                                      dict_to_delete)
    postgres_client.delete_from_table(POSTGRES_DATABASE, "noisy_info",
                                      dict_to_delete)

    files = glob.glob(f'output/**/*_{model}*', recursive=True)
    for f in files:
        os.remove(f)
