# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\__init__.py                                                                  #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Friday, April 3rd 2026, 9:17:38 PM                                                                    #
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

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS, CONF_IP, CONF_PORT, CONF_PROTO, CONF_USER, CONF_PASS, CONF_DEVICE_INFO
from .hub import TesiraHub
from .util import gen_hub_key, parse_hub_key

_LOGGER = logging.getLogger(__name__)

DATA_HUBS = "hubs"
DATA_ENTRY_HUBKEY = "entry_hubkey"
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_HUBS, {})
    hass.data[DOMAIN].setdefault(DATA_ENTRY_HUBKEY, {})
    return True

async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # Options changed (controls added/edited/removed) → reload entities
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_IP]
    port = entry.data[CONF_PORT]
    proto = entry.data[CONF_PROTO]
    user = entry.data.get(CONF_USER)
    pwrd = entry.data.get(CONF_PASS)
    device_info = entry.data.get(CONF_DEVICE_INFO)

    hubs: dict[str, TesiraHub] = hass.data[DOMAIN][DATA_HUBS]
    hubkey = gen_hub_key(deviceModel=device_info.get("deviceModel"), deviceRevision=device_info.get("deviceRevision"), serialNumber=device_info.get("serialNumber"))
    hub = hubs.get(hubkey)
    if hub is None:
        hub = TesiraHub(host=host, port=port, proto=proto, username=user, password=pwrd, safe_mode=True)
        hubs[hubkey] = hub
        _LOGGER.debug("Created Tesira hub for %s", hubkey)

    hass.data[DOMAIN][DATA_ENTRY_HUBKEY][entry.entry_id] = hubkey

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hubkey = hass.data[DOMAIN][DATA_ENTRY_HUBKEY].pop(entry.entry_id, None)
    if hubkey:
        hubs: dict[str, TesiraHub] = hass.data[DOMAIN][DATA_HUBS]
        # If no other entries reference this hubkey, close it.
        if hubkey not in hass.data[DOMAIN][DATA_ENTRY_HUBKEY].values():
            hub = hubs.pop(hubkey, None)
            if hub:
                await hub.disconnect()
                _LOGGER.debug("Closed Tesira hub for %s", hubkey)

    return unload_ok
