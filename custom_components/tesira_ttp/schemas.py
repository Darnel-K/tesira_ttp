# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\schemas.py                                                                   #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Sunday, April 5th 2026, 9:10:10 PM                                                                    #
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
from .const import (
    DOMAIN,
    CONF_IP,
    CONF_PORT,
    CONF_PROTO,
    CONF_USER,
    CONF_PASS,
    DEFAULT_IP,
    DEFAULT_PORT,
    DEFAULT_PROTO,
    DEFAULT_USER,
    DEFAULT_PASS,
    CONF_CONTROL_NAME,
    CONF_INSTANCE_TAG,
    CONF_CHANNEL,
    CONF_MIN_DB,
    CONF_MAX_DB,
    CONF_STEP_DB,
    DEFAULT_CONTROL_NAME,
    DEFAULT_CHANNEL,
    DEFAULT_MIN_DB,
    DEFAULT_MAX_DB,
    DEFAULT_STEP_DB
)

_LOGGER = logging.getLogger(__name__)

def _device_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_IP, default=d.get(CONF_IP, DEFAULT_IP)): cv.string,
            vol.Optional(CONF_PORT, default=d.get(CONF_PORT, DEFAULT_PORT)): cv.port,
            vol.Required(CONF_PROTO, default=d.get(CONF_PROTO, DEFAULT_PROTO)): selector({
                "select": {
                    "options": [
                        {"value": "ssh", "label": "SSH"},
                        {"value": "telnet", "label": "Telnet"}
                    ]
                }
            }),
            vol.Optional(CONF_USER, default=d.get(CONF_USER, DEFAULT_USER)): cv.string,
            vol.Optional(CONF_PASS, default=d.get(CONF_PASS, DEFAULT_PASS)): cv.string
        }
    )

def _control_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Optional(CONF_CONTROL_NAME, default=d.get(CONF_CONTROL_NAME, DEFAULT_CONTROL_NAME)): cv.string,
            vol.Required(CONF_INSTANCE_TAG, default=d.get(CONF_INSTANCE_TAG, "volume")): cv.string,
            vol.Optional(CONF_CHANNEL, default=int(d.get(CONF_CHANNEL, DEFAULT_CHANNEL))): vol.Coerce(int),
            vol.Optional(CONF_MIN_DB, default=float(d.get(CONF_MIN_DB, DEFAULT_MIN_DB))): vol.Coerce(float),
            vol.Optional(CONF_MAX_DB, default=float(d.get(CONF_MAX_DB, DEFAULT_MAX_DB))): vol.Coerce(float),
            vol.Optional(CONF_STEP_DB, default=float(d.get(CONF_STEP_DB, DEFAULT_STEP_DB))): vol.Coerce(float),
        }
    )
