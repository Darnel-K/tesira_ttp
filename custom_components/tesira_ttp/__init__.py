# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\__init__.py                                                                  #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Wednesday, April 15th 2026, 9:23:26 PM                                                                #
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
import copy

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, PLATFORMS, DICT_KEYS, DEFAULTS
from .hub import TesiraHub

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # Keep integration state in hass.data so all platforms can share hubs and lookup keys.
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DICT_KEYS["DATA_HUBS"], {})
    hass.data[DOMAIN].setdefault(DICT_KEYS["DATA_ENTRY_HUBKEY"], {})
    return True

async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # Reload platforms when options change.
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Validate config entry data and create/reuse a hub instance for this entry.
    devices = copy.deepcopy(entry.data.get(DICT_KEYS["DEVICES"], DEFAULTS["DEVICES"]))
    primary_device_id = devices.get("primary")
    if not primary_device_id or primary_device_id not in devices["items"]:
        _LOGGER.error("Invalid or missing primary device in config entry %s", entry.entry_id)
        return False
    primary_device = devices["items"][primary_device_id]
    conn_info = primary_device["connection_info"]
    auth_credentials = conn_info.get("auth", {})
    host = conn_info.get(DICT_KEYS["HOST"])
    port = conn_info.get(DICT_KEYS["PORT"])
    proto = conn_info.get(DICT_KEYS["PROTO"])
    user = auth_credentials.get(DICT_KEYS["USER"])
    pwrd = auth_credentials.get(DICT_KEYS["PASS"])

    # Hub key is currently tied to entry_id, but we still centralize lifecycle in hass.data.
    hubs: dict[str, TesiraHub] = hass.data[DOMAIN][DICT_KEYS["DATA_HUBS"]]
    hubkey = entry.entry_id
    hub = hubs.get(hubkey)
    if hub is None:
        # No existing hub for this entry, create a new one
        hub = TesiraHub(host=host, port=port, proto=proto, username=user, password=pwrd, safe_mode=True)
        hubs[hubkey] = hub
        _LOGGER.debug("Created Tesira hub for %s", hubkey)

    # Store the hubkey for this entry to manage shared hubs across entries
    hass.data[DOMAIN][DICT_KEYS["DATA_ENTRY_HUBKEY"]][entry.entry_id] = hubkey

    # Register all configured devices so entities can attach to a stable HA device record.
    device_registry = dr.async_get(hass)
    for device_id, device in devices["items"].items():
        device_info = device.get("device_info", {})
        device_registry.async_get_or_create(config_entry_id=entry.entry_id, identifiers={(DOMAIN, device_id)}, manufacturer=device_info.get("manufacturer"), model=device_info.get("model"), model_id=device_info.get("model_id"), name=device_info.get('name'), sw_version=device_info.get("sw_version"), hw_version=device_info.get("hw_version"), serial_number=device_info.get("serial_number"))

    # Set up update listener for options changes
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

# Unload platforms and release hub resources when an entry is removed or disabled.
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove the hubkey for this entry and check if we need to close the hub
    hubkey = hass.data[DOMAIN][DICT_KEYS["DATA_ENTRY_HUBKEY"]].pop(entry.entry_id, None)
    if hubkey:
        # Check if any other entries still reference this hubkey before disconnecting
        hubs: dict[str, TesiraHub] = hass.data[DOMAIN][DICT_KEYS["DATA_HUBS"]]
        # If no other entries reference this hubkey, close it.
        if hubkey not in hass.data[DOMAIN][DICT_KEYS["DATA_ENTRY_HUBKEY"]].values():
            hub = hubs.pop(hubkey, None)
            if hub:
                await hub.disconnect()
                _LOGGER.debug("Closed Tesira hub for %s", hubkey)

    return unload_ok
