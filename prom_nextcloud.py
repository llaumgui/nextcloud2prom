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

import requests
from prometheus_client import CollectorRegistry, Gauge, generate_latest

# Configuration
NC_URL = 'https://cloud.domain.ltd/ocs/v2.php/apps/serverinfo/api/v1/info?format=json'
NC_TOKEN = 'token'


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
    Nextclud instance is up ?
    """
    try:
        status = 1 if json_info['ocs']['meta']['status'] == "ok" else 0
    except TypeError:
        status = 0
        pass

    Gauge('nextcloud_status', "Nextcloud is OK ?", registry=registry).set(status)


def _write_storage(registry, json_info):
    """
    Nextcloud storage information.
    """
    for storage, value in json_info['ocs']['data']['nextcloud']['storage'].items():
        Gauge('nextcloud_storage_' + storage, f"Nextcloud storage `{storage}` information.",
                                              registry=registry).set(value)


def _write_shares(registry, json_info):
    """
    Nextcloud storage information.
    """
    for share, value in json_info['ocs']['data']['nextcloud']['shares'].items():
        Gauge('nextcloud_shares_' + share, f"Nextcloud shares `{share}` information.",
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
        _write_storage(registry, json_info)
        _write_shares(registry, json_info)
        _write_active_users(registry, json_info)

    print(generate_latest(registry).decode(), end='')


if __name__ == "__main__":
    _main()
