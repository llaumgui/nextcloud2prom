#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2024 Guillaume Kulakowski <guillaume@kulakowski.fr>
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

    __json_info = dict
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
        Is Nextcloud instance is up ?
        """

        try:
            status = 1 if self.__json_info['ocs']['meta']['status'] == "ok" else 0
        except TypeError:
            status = 0
            pass

        Gauge('nextcloud_status', "Nextcloud is OK ?", registry=self.__registry).set(status)

    def __json_iterator(self, part_json: dict, part_id: str, part_title: str):
        """
        Display iterative information from part of JSON.
        """
        for item, item_value in part_json:
            info_data = {}
            item_id = item.replace(".", "_")
            current_id = f"{part_id}_{item_id}"
            current_title = f"{part_title} `{item}` information."

            # For string
            if isinstance(item_value, str):
                info_data[item] = item_value

            # For numeric
            elif isinstance(item_value, int):
                Gauge(current_id, current_title, registry=self.__registry).set(item_value)

            # For list
            elif isinstance(item_value, list) and isinstance(list[0], int):
                g = Gauge(current_id, current_title, [item], registry=self.__registry)
                for list_item, list_item_value in enumerate(item_value):
                    g.labels(list_item).set(list_item_value)

            # For dict
            elif isinstance(item_value, dict):
                # Recurtion
                self.__json_iterator(item_value.items(), current_id, current_title)

            # "Dump" informations
            if info_data:
                Info(current_id, current_title, registry=self.__registry).info(info_data)


def _main():
    """
    Main function.
    """
    collector = Collector()
    collector.print()


if __name__ == "__main__":
    _main()
