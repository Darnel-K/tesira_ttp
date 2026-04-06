# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\util.py                                                                      #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Sunday, April 5th 2026, 9:19:42 PM                                                                    #
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
"""Utility helpers for tesira_ttp."""

from __future__ import annotations

from typing import Dict

import base64
import json

def gen_hub_key(deviceModel: str, deviceRevision: int, serialNumber: str, format: str = "b64") -> str:
    """
    Generate a unique key for a Tesira hub based on connection parameters.

    Args:

        deviceModel: The model of the device.
        deviceRevision: The revision of the device.
        serialNumber: The serial number of the device.
        format: The output format of the key ("b64" for base64, "plain" for raw string, "json" for JSON).

    Returns:
        A unique string key representing the hub configuration.
    """
    ALLOWED_FORMATS = {"b64", "plain", "json"}
    hub_key = {"deviceModel": deviceModel.lower(), "deviceRevision": deviceRevision.lower(), "serialNumber": serialNumber.lower()}
    format = format.lower().strip()
    if format not in ALLOWED_FORMATS:
            raise ValueError(f"Unsupported format '{format}'. Allowed: {ALLOWED_FORMATS}")

    match format:
        case "json":
             return json.dumps(hub_key, sort_keys=True)
        case "plain":
             return f"{hub_key['deviceModel']}:{hub_key['deviceRevision']}:{hub_key['serialNumber']}"
        case "b64":
             return base64.urlsafe_b64encode(json.dumps(hub_key, sort_keys=True).encode()).decode()

def parse_hub_key(hub_key: str, format: str = "b64") -> Dict[str, str]:
    """
    Parse a hub key back into its components.

    Args:
        hub_key: The unique key representing the hub configuration.
        format: The format of the input key ("b64" for base64, "plain" for raw string, "json" for JSON).

    Returns:
        A dictionary containing the original parameters (deviceModel, deviceRevision, serialNumber).
    """
    ALLOWED_FORMATS = {"b64", "plain", "json"}
    format = format.lower().strip()
    if format not in ALLOWED_FORMATS:
            raise ValueError(f"Unsupported format '{format}'. Allowed: {ALLOWED_FORMATS}")

    match format:
        case "json":
             return json.loads(hub_key)
        case "plain":
             parts = hub_key.split(":")
             if len(parts) != 3:
                 raise ValueError("Invalid plain format. Expected 'deviceModel:deviceRevision:serialNumber'")
             return {"deviceModel": parts[0], "deviceRevision": parts[1], "serialNumber": parts[2]}
        case "b64":
             decoded = base64.urlsafe_b64decode(hub_key.encode()).decode()
             return json.loads(decoded)

class TesiraTTPException(Exception):
    """Base exception for tesira_ttp."""
    class NotPermitted(Exception):
        """Raised when an action is not permitted by the integration."""
        pass
