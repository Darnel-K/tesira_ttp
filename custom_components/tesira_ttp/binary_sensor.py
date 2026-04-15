# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\binary_sensor.py                                                             #
# Repository: tesira_ttp                                                                                               #
# Created Date: Saturday, March 28th 2026, 10:45:20 PM                                                                 #
# Last Modified: Wednesday, April 15th 2026, 12:28:40 AM                                                               #
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
import asyncio
import copy
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DICT_KEYS, DEFAULTS
from .hub import TesiraHub

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    hubkey = entry.entry_id
    hub: TesiraHub = hass.data[DOMAIN][DICT_KEYS["DATA_HUBS"]][hubkey]
    devices = copy.deepcopy(entry.data.get(DICT_KEYS["DEVICES"], DEFAULTS["DEVICES"]))
    entities = copy.deepcopy(entry.options.get(DICT_KEYS["ENTITIES"], DEFAULTS["ENTITIES"]))
    entities_list = []

    for block_type, item_list in entities.items():
        for item in item_list:
            if "binary_sensor" in item["supported_entity_types"]:
                 pass


    entities_list.append(TesiraHubConnBinarySensor(hub, hubkey))

    for device_id, device in devices["items"].items():
        entities_list.append(TesiraNetConnBinarySensor(hub, device_id, device))

    async_add_entities(entities_list, update_before_add=True)

class TesiraNetConnBinarySensor(BinarySensorEntity):
    """Binary sensor for Tesira connection status."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_should_poll = True

    def __init__(self, hub: TesiraHub, device_id: str, device: dict) -> None:
        self._hub = hub
        self._device_id = device_id
        self._device = device
        self._device_info = device.get("device_info", {})
        self._device_connection_info = device.get("connection_info", {})
        self._attr_name = f"Network Connection Status ({self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._device_id[:10]}_netconnstate".lower()
        self._attr_is_on = False
        self._attr_available = True

    @property
    def is_on(self) -> bool | None:
            return self._attr_is_on

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device_id)}}

    async def _async_ping(self, host: str) -> bool:
        """Ping the host using the OS ping command."""
        # On Linux/HA OS: ping -c 1 -W 1 <host>
        #   -c 1 : send 1 packet
        #   -W 1 : timeout after 1 second
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "1", host,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    async def async_update(self):
        self._attr_is_on = await self._async_ping(self._device_connection_info.get(DICT_KEYS["HOST"]))

class TesiraHubConnBinarySensor(BinarySensorEntity):
    """Binary sensor for Tesira hub connection status."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_should_poll = True

    def __init__(self, hub: TesiraHub, hubkey: str) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._attr_name = f"Hub Connection Status ({self._hubkey[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10]}_hubconnstate".lower()
        self._attr_is_on = False
        self._attr_available = True

    @property
    def is_on(self) -> bool | None:
            return self._attr_is_on

    async def async_update(self):
        self._attr_is_on = self._hub.is_connected
