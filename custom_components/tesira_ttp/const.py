# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\const.py                                                                     #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Sunday, April 12th 2026, 10:05:47 PM                                                                  #
# Original Author: Darnel Kumar                                                                                        #
# Author Github: https://github.com/Darnel-K                                                                           #
#                                                                                                                      #
# License: GNU Affero General Public License v3.0 only - https://www.gnu.org/licenses/agpl.txt                         #
# Copyright (c) 2026 Darnel Kumar                                                                                      #
#                                                                                                                      #
# This program is free software: you can redistribute it and/or modify                                                 #
# it under the terms of the GNU Affero General Public License as published                                             #
# by the Free Software Foundation, either version 3 of the License, or                                                 #
# (at your option) any later version.                                                                                  #
#                                                                                                                      #
# This program is distributed in the hope that it will be useful,                                                      #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                                                       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                                        #
# GNU Affero General Public License for more details.                                                                  #
#                                                                                                                      #
# You should have received a copy of the GNU Affero General Public License                                             #
# along with this program.  If not, see <https://www.gnu.org/licenses/>.                                               #
# #################################################################################################################### #
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "tesira_ttp"
PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.BINARY_SENSOR]

DICT_KEYS = {
    "DATA_HUBS": "hubs",
    "DATA_ENTRY_HUBKEY": "entry_hubkey",
    "HUB_TITLE": "hub_title",
    "HOST": "host",
    "PORT": "port",
    "PROTO": "protocol",
    "USER": "username",
    "PASS": "password",
    "DEVICE_INFO": "device_info",
    "CONTROLS": "controls",
    "DEVICES": "devices",
    "ENTITIES": "entities",
    "CONTROL_NAME": "name",
    "INSTANCE_TAG": "instance_tag",
    "CHANNEL": "channel",
    "MIN_DB": "min_db",
    "MAX_DB": "max_db",
    "STEP_DB": "step_db"
}

CONFIG_MODES = {
    "INIT": "init",
    "RECONFIGURE": "reconfigure"
}

DEFAULT_DEVICES = {
    "items": {},
    "primary": None
}

DEFAULT_ENTITIES = {
    "block_type": []
}

DEFAULTS = {
    "HOST": "0.0.0.0",
    "PORT": 22,
    "PROTO": "ssh",
    "USER": "default",
    "PASS": "",
    "CONTROL_NAME": "Tesira Volume",
    "CHANNEL": 1,
    "MIN_DB": -100.0,
    "MAX_DB": 12.0,
    "STEP_DB": 0.5,
    "DEVICES": DEFAULT_DEVICES,
    "ENTITIES": DEFAULT_ENTITIES
}
