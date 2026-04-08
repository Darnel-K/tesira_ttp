# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\util.py                                                                      #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Tuesday, April 7th 2026, 11:21:40 PM                                                                  #
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

from typing import Dict, Any
from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_PROTO, CONF_USER, CONF_PASS

import base64
import json
import copy

def gen_device_dict(host: str, port: int, proto: str, user: str, pwrd: str, device_info: dict, device_id: str = None) -> Dict[str, Any]:
    """
    Generate a dictionary template for a Tesira device.

    Returns:
        A dictionary with the structure for storing device information and connection details.
    """
    if device_id is None:
        device_id = gen_device_id(device_info["deviceModel"], device_info["deviceRevision"], device_info["serialNumber"])
    return {
        "connection_info": {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_PROTO: proto,
            "auth": {
                CONF_USER: user,
                CONF_PASS: pwrd
            }
        },
        "device_info": {
            "name": f"Biamp - {device_info['deviceModel']} - {device_info['serialNumber']} - {host}:{port}",
            "manufacturer": "Biamp",
            "model": device_info["deviceModel"],
            "model_id": device_info["deviceModel"],
            "sw_version": device_info["firmwareVersion"],
            "hw_version": device_info["deviceRevision"],
            "serial_number": device_info["serialNumber"]
        }
    }

def _redact_device(device: dict[str, Any]) -> dict[str, Any]:
    redacted = copy.deepcopy(device)
    auth = redacted.get("connection_info", {}).get("auth")
    if auth:
        auth[CONF_USER] = "***"
        auth[CONF_PASS] = "***"
    return redacted


def gen_device_id(deviceModel: str, deviceRevision: int, serialNumber: str, format: str = "b64") -> str:
    """
    Generate a unique key for a Tesira device based on its properties.

    Args:

        deviceModel: The model of the device.
        deviceRevision: The revision of the device.
        serialNumber: The serial number of the device.
        format: The output format of the key ("b64" for base64, "plain" for raw string, "json" for JSON).

    Returns:
        A unique string key representing the device configuration.
    """
    ALLOWED_FORMATS = {"b64", "plain", "json"}
    device_id = {"deviceModel": deviceModel.lower(), "deviceRevision": deviceRevision.lower(), "serialNumber": serialNumber.lower()}
    format = format.lower().strip()
    if format not in ALLOWED_FORMATS:
            raise ValueError(f"Unsupported format '{format}'. Allowed: {ALLOWED_FORMATS}")

    match format:
        case "json":
             return json.dumps(device_id, sort_keys=True)
        case "plain":
             return f"{device_id['deviceModel']}:{device_id['deviceRevision']}:{device_id['serialNumber']}"
        case "b64":
             return base64.urlsafe_b64encode(json.dumps(device_id, sort_keys=True).encode()).decode()

def parse_device_id(device_id: str, format: str = "b64") -> Dict[str, str]:
    """
    Parse a device ID back into its components.

    Args:
        device_id: The unique ID representing the device configuration.
        format: The format of the input ID ("b64" for base64, "plain" for raw string, "json" for JSON).

    Returns:
        A dictionary containing the original parameters (deviceModel, deviceRevision, serialNumber).
    """
    ALLOWED_FORMATS = {"b64", "plain", "json"}
    format = format.lower().strip()
    if format not in ALLOWED_FORMATS:
            raise ValueError(f"Unsupported format '{format}'. Allowed: {ALLOWED_FORMATS}")

    match format:
        case "json":
             return json.loads(device_id)
        case "plain":
             parts = device_id.split(":")
             if len(parts) != 3:
                 raise ValueError("Invalid plain format. Expected 'deviceModel:deviceRevision:serialNumber'")
             return {"deviceModel": parts[0], "deviceRevision": parts[1], "serialNumber": parts[2]}
        case "b64":
             decoded = base64.urlsafe_b64decode(device_id.encode()).decode()
             return json.loads(decoded)

class TesiraTTPException(Exception):
    """Base exception for tesira_ttp."""
    class NotPermitted(Exception):
        """Raised when an action is not permitted by the integration."""
        pass
