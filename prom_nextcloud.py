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
NC_URL = os.getenv('NC_URL', 'https://cloud.domain.ltd/ocs/v2.php/apps/serverinfo/api/v1/info?format=json')
NC_TOKEN = os.getenv('NC_TOKEN', 'NC_TOKEN')


def _load_json_info():
    """
    Load JSON information from Nextcloud.
    """

    headers = {
        "NC-Token": NC_TOKEN
    }
    response = requests.get(NC_URL, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return False


def _write_status(registry, json_info):
    """
    Is Nextcloud instance is up ?
    """
    try:
        status = 1 if json_info['ocs']['meta']['status'] == "ok" else 0
    except TypeError:
        status = 0
        pass

    Gauge('nextcloud_status', "Nextcloud is OK ?", registry=registry).set(status)


def _write_system(registry, json_info):
    """
    Nextcloud system information.
    """
    i = Info('nextcloud_system', 'Nextcloud system informationq.', registry=registry)
    info_data = {}

    for system, value in json_info['ocs']['data']['nextcloud']['system'].items():
        # For string
        if isinstance(value, str):
            info_data[system] = value
        # For numeric
        elif isinstance(value, int):
            Gauge(f"nextcloud_system_{system}_bytes",
                  f"Nextcloud system `{system}` information.",
                  registry=registry).set(value)
        # For cpuload list
        elif isinstance(value, list) and system == 'cpuload':
            g = Gauge(f"nextcloud_system_{system}",
                      f"Nextcloud system `{system}` information.",
                      ['cpu'],
                      registry=registry)
            for item, item_value in enumerate(value):
                g.labels(item).set(item_value)

        i.info(info_data)


def _write_storage(registry, json_info):
    """
    Nextcloud storage information.
    """
    for storage, value in json_info['ocs']['data']['nextcloud']['storage'].items():
        Gauge(f"nextcloud_storage_{storage}_total",
              f"Nextcloud storage `{storage}` information.",
              registry=registry).set(value)


def _write_shares(registry, json_info):
    """
    Nextcloud shares information.
    """
    for share, value in json_info['ocs']['data']['nextcloud']['shares'].items():
        Gauge(f"nextcloud_shares_{share}_total",
              f"Nextcloud shares `{share}` information.",
              registry=registry).set(value)


def _write_active_users(registry, json_info):
    """
    Nextcloud active users information.
    """
    Gauge('nextcloud_active_users_5m', "Nextcloud active users last 5 minuts.",
                                       registry=registry).set(json_info['ocs']['data']['activeUsers']['last5minutes'])
    Gauge('nextcloud_active_users_1h', "Nextcloud active users last 1 hour.",
                                       registry=registry).set(json_info['ocs']['data']['activeUsers']['last1hour'])
    Gauge('nextcloud_active_users_1d', "Nextcloud active users last 24 hours.",
                                       registry=registry).set(json_info['ocs']['data']['activeUsers']['last24hours'])


def _main():
    """
    Main function.
    """
    json_info = _load_json_info()

    registry = CollectorRegistry()
    _write_status(registry, json_info)
    if json_info is not False:
        _write_system(registry, json_info)
        _write_storage(registry, json_info)
        _write_shares(registry, json_info)
        _write_active_users(registry, json_info)

    print(generate_latest(registry).decode(), end='')


if __name__ == "__main__":
    _main()
