import os
import urllib
import urllib.parse
import json
import datetime
from typing import List, Tuple, Optional
import time

import pandas as pd
import requests

from iams.infra.monitoring.log import start_logging

logger = start_logging()

MESSAGE = "message"


class GrafanaClient:
    """
    This class is used to do actions in Grafana as create annotations, list dashboards, etc.
    """

    def __init__(self, grafana_url: str, grafana_api_key: str):
        self.verify = False
        self.__grafana_url = "https://" + grafana_url
        self.__header = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + grafana_api_key
        }

    def annotate_from_dataframe(self, dashboard_name: str, panel_name: str, annotation_dataframe: pd.DataFrame) -> None:
        """
        This creates all annotations on panel_name in dashboard_name from annotation_dataframe.
        """
        dashboard_id, dashboard_uid = self.get_dashboard_id_and_uid(dashboard_name)
        panel_id = self.get_panel_id(dashboard_uid=dashboard_uid, panel_name=panel_name)
        for _, row in annotation_dataframe.iterrows():
            self.create_annotation(
                time_from=str(row["time"]),
                time_to=str(row["end_time"]),
                title=row["comments"],
                tags_list=[row["anomaly_type"], "ongoing" if row["ongoing"] else "terminated"],
                dashbord_id=dashboard_id,
                panel_id=panel_id
            )

    def create_annotation(self, dashbord_id: str, panel_id: str, time_from: str, time_to: str,
                          title: str, tags_list: List[str]) -> None:
        """Create annotation on Grafana with specified parameters."""
        # TODO: replace as it might break if we change date format
        time_from = datetime.datetime.strptime(time_from, '%Y-%m-%d %H:%M:%S')
        start_time = int(time_from.strftime("%s")) * 1000
        time_to = datetime.datetime.strptime(time_to, '%Y-%m-%d %H:%M:%S')
        end_time = int(time_to.strftime("%s")) * 1000

        url = os.path.join(self.__grafana_url, "api/annotations")
        payload = {
            "dashboardId": dashbord_id,
            "panelId": panel_id,
            "time": start_time,
            "timeEnd": end_time,
            "tags": tags_list,
            "text": title
        }
        payload = json.dumps(payload)

        try:
            response = requests.post(url, headers=self.__header, data=payload, verify=self.verify)
        except requests.RequestException as e:
            logger.error("ERROR:", e)
            raise

        logger.info(f"JSON response received from the POST to API service 'api/annotations' :\n{response.json()}")

    def get_dashboard_id_and_uid(self, dashboard_name: str) -> Optional[Tuple[str, str]]:
        """Returns dashboard id and uid from given dashboard_name"""
        url = os.path.join(self.__grafana_url, "api/search?query=" + urllib.parse.quote(dashboard_name))

        try:
            response = requests.get(url, headers=self.__header, verify=self.verify)
        except requests.RequestException as e:
            logger.error("ERROR:", e)
            raise

        logger.info(f"JSON response received from the POST to API service 'api/search', "
                    f"with dashboard name = '{dashboard_name}'' :\n{response.json()}")

        if 'message' in response.json():
            return None, None

        return response.json()[0]['id'], response.json()[0]['uid']

    def get_panel_id(self, dashboard_uid: str, panel_name: str) -> Optional[str]:
        """Returns id of given Grafana panel_name from specified dashboard_uid."""
        url = os.path.join(self.__grafana_url, "api/dashboards/uid", dashboard_uid)

        try:
            response = requests.get(url, headers=self.__header, verify=self.verify)
        except requests.RequestException as e:
            logger.error("ERROR:", e)
            raise

        logger.info(f"JSON response received from the POST to API service 'api/dashboards/uid', "
                    f"with dashboard uid = '{dashboard_uid}'' :\n{response.json()}")

        if 'message' in response.json():
            return None

        panels = response.json()['dashboard']['panels']
        for p in panels:
            if p['title'].strip() == panel_name:
                return p['id']
        return None

    def get_annotation_ids_filtered_by(self, tags_list: list) -> List[Optional[int]]:
        """Returns all annotations ids having tags matching tags_list."""
        tags_api_query = "api/annotations?tags=" + "&tags=".join(tags_list)
        url = os.path.join(self.__grafana_url, tags_api_query)

        try:
            response = requests.get(url, headers=self.__header, data={}, verify=self.verify)
        except requests.RequestException as e:
            logger.error("ERROR:", e)
            raise

        logger.info(f"JSON response received from the POST to API service 'api/annotations', "
                    f"with tags = '{tags_list}'' :\n{response.json()}")

        return [annotation["id"] for annotation in response.json()]

    def patch_annotation(self, annotation_id: int, updated_timestamp: Optional[str] = None,
                         new_tags_list: Optional[list] = None) -> requests.models.Response:
        """Update grafana annotation with data given in updated_timestamp & new_tags_list."""
        url = os.path.join(self.__grafana_url, f"api/annotations/{annotation_id}")
        logger.info(f"Updating data for {annotation_id}")
        patch_data = {}
        if updated_timestamp:
            # TODO: replace as it might break if we change date format
            unix_timestamp_ms = int(time.mktime(datetime.datetime.strptime(
                updated_timestamp, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000
            patch_data["timeEnd"] = unix_timestamp_ms
        if new_tags_list:
            patch_data["tags"] = new_tags_list
        patch_data = json.dumps(patch_data)
        try:
            response = requests.patch(url, headers=self.__header, data=patch_data, verify=self.verify)
            logger.info(f"Api response call: {response.status_code}")
            logger.info("API call sent with data:")
            logger.info(patch_data)
        except requests.RequestException as e:
            logger.error("ERROR:", e)
            raise
        logger.info(f"JSON response received from the POST to API service 'api/annotations', "
                    f"with annotation id = '{annotation_id}'' :\n{response.json()}")
        return response
