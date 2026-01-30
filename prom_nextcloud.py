#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2026 Guillaume Kulakowski <guillaume@kulakowski.fr>
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.
#

"""
Description: Expose metrics from Nextcloud application server info in JSON format.
"""

import os
import requests
from prometheus_client import CollectorRegistry, Gauge, Info, generate_latest

# Configuration
NC_URL = os.getenv('NC_URL')
NC_TOKEN = os.getenv('NC_TOKEN')
if not NC_URL or not NC_TOKEN:
    print("Please setup NC_URL and NC_TOKEN in your prom-nextcloud.service file.")
    exit(1)


class Collector:

    __json_info = None
    __registry = CollectorRegistry()

    def __init__(self):
        self.__json_info = self.__load_json_info()
        self.__write_status()

        if self.__json_info is not False:
            # 'nextcloud' part
            self.__json_iterator(self.__json_info['ocs']['data']['nextcloud'].items(),
                                 'nextcloud',
                                 'Nextcloud')
            self.__json_iterator(self.__json_info['ocs']['data']['server'].items(),
                                 'nextcloud_server',
                                 'Nextcloud server')
            self.__json_iterator(self.__json_info['ocs']['data']['activeUsers'].items(),
                                 'nextcloud_active_users',
                                 'Nextcloud active users')

    def __load_json_info(self):
        """
        Load JSON information from Nextcloud server info application.
        """
        headers = {
            "NC-Token": NC_TOKEN
        }
        response = requests.get(NC_URL, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return False

    def print(self):
        """
        Print registry.
        """
        print(generate_latest(self.__registry).decode(), end='')

    def __write_status(self):
        """
        Is Nextcloud instance up?
        """
        try:
            status = 1 if self.__json_info['ocs']['meta']['status'] == "ok" else 0
        except TypeError:
            status = 0
            pass

        Gauge('nextcloud_status', "Nextcloud is OK ?", registry=self.__registry).set(status)

    def __json_iterator(self, part_json: dict, part_id: str, part_title: str):
        """
        Recursively walk JSON and export metrics.
        Expects part_json to be an iterable of (key, value) pairs (e.g. dict.items()).
        """
        info_data = {}

        for item, item_value in part_json:
            # Create safe metric id
            item_id = str(item).replace(".", "_").replace("-", "_")
            current_id = f"{part_id}_{item_id}"
            current_title = f"{part_title} `{item}` information."

            # Skip None
            if item_value is None:
                continue

            # For booleans -> export as 1/0
            if isinstance(item_value, bool):
                Gauge(current_id, current_title, registry=self.__registry).set(1 if item_value else 0)
                continue

            # For numeric types (int, float)
            if isinstance(item_value, (int, float)) and not isinstance(item_value, bool):
                Gauge(current_id, current_title, registry=self.__registry).set(item_value)
                continue

            # For string -> collect into Info (dumped later)
            if isinstance(item_value, str):
                info_data[item_id] = item_value
                continue

            # For lists
            if isinstance(item_value, list):
                # Empty list -> skip
                if len(item_value) == 0:
                    continue

                # If list of numerics -> create a gauge with index label
                if all(isinstance(x, (int, float)) for x in item_value):
                    g = Gauge(current_id, current_title, ['index'], registry=self.__registry)
                    for idx, val in enumerate(item_value):
                        g.labels(index=str(idx)).set(val)
                    continue

                # If list of strings -> either create info entries or labelled metrics (here: as info with numbered keys)
                if all(isinstance(x, str) for x in item_value):
                    # Put into info_data as a comma-separated list
                    info_data[item_id] = ",".join(item_value)
                    continue

                # Mixed types -> store repr
                info_data[item_id] = str(item_value)
                continue

            # For dicts
            if isinstance(item_value, dict):
                # Detect dict with numeric keys (like extensions: "0":"Core", "1":"date", ...)
                keys = list(item_value.keys())
                if keys and all(k.isdigit() for k in keys):
                    # Values are expected to be strings (extension names). Export as labelled metric:
                    # nextcloud_server_php_extensions{extension="apcu"} 1
                    g = Gauge(current_id, current_title, ['extension'], registry=self.__registry)
                    for k in sorted(keys, key=lambda x: int(x)):
                        v = item_value[k]
                        if isinstance(v, str):
                            g.labels(extension=v).set(1)
                        else:
                            # fallback: convert to string
                            g.labels(extension=str(v)).set(1)
                    continue

                # Normal dict -> recurse
                self.__json_iterator(item_value.items(), current_id, current_title)
                continue

            # Fallback: put string representation into info
            info_data[item_id] = str(item_value)

        # "Dump" informations as Info() if any strings were collected
        if info_data:
            # Info metric name must be unique per part_id
            try:
                Info(part_id, part_title, registry=self.__registry).info(info_data)
            except ValueError:
                # If Info with same name already exists, skip or handle as needed
                pass


def _main():
    """
    Main function.
    """
    collector = Collector()
    collector.print()


if __name__ == "__main__":
    _main()
