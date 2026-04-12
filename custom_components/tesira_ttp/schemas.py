# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\schemas.py                                                                   #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Sunday, April 12th 2026, 10:09:23 PM                                                                  #
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

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from typing import Any
from homeassistant.helpers.selector import selector
from .const import DOMAIN, DICT_KEYS, DEFAULTS

_LOGGER = logging.getLogger(__name__)

def _hub(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(DICT_KEYS["HUB_TITLE"], default=d.get(DICT_KEYS["HUB_TITLE"], "")): cv.string
        }
    )

def _device_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(DICT_KEYS["HOST"], default=d.get(DICT_KEYS["HOST"], DEFAULTS["HOST"])): cv.string,
            vol.Optional(DICT_KEYS["PORT"], default=d.get(DICT_KEYS["PORT"], DEFAULTS["PORT"])): cv.port,
            vol.Required(DICT_KEYS["PROTO"], default=d.get(DICT_KEYS["PROTO"], DEFAULTS["PROTO"])): selector({
                "select": {
                    "options": [
                        {"value": "ssh", "label": "SSH"},
                        {"value": "telnet", "label": "Telnet"}
                    ]
                }
            }),
            vol.Optional(DICT_KEYS["USER"], default=d.get(DICT_KEYS["USER"], DEFAULTS["USER"])): cv.string,
            vol.Optional(DICT_KEYS["PASS"], default=d.get(DICT_KEYS["PASS"], DEFAULTS["PASS"])): cv.string
        }
    )

def _control_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Optional(DICT_KEYS["CONTROL_NAME"], default=d.get(DICT_KEYS["CONTROL_NAME"], DEFAULTS["CONTROL_NAME"])): cv.string,
            vol.Required(DICT_KEYS["INSTANCE_TAG"], default=d.get(DICT_KEYS["INSTANCE_TAG"], "volume")): cv.string,
            vol.Optional(DICT_KEYS["CHANNEL"], default=int(d.get(DICT_KEYS["CHANNEL"], DEFAULTS["CHANNEL"]))): vol.Coerce(int),
            vol.Optional(DICT_KEYS["MIN_DB"], default=float(d.get(DICT_KEYS["MIN_DB"], DEFAULTS["MIN_DB"]))): vol.Coerce(float),
            vol.Optional(DICT_KEYS["MAX_DB"], default=float(d.get(DICT_KEYS["MAX_DB"], DEFAULTS["MAX_DB"]))): vol.Coerce(float),
            vol.Optional(DICT_KEYS["STEP_DB"], default=float(d.get(DICT_KEYS["STEP_DB"], DEFAULTS["STEP_DB"]))): vol.Coerce(float),
        }
    )
