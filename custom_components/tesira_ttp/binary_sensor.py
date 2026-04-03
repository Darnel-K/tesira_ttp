# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\binary_sensor.py                                                             #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Saturday, April 4th 2026, 12:03:22 AM                                                                 #
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
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_IP, CONF_PORT, CONF_DEVICE_INFO
from .hub import TesiraHub
from .util import gen_hub_key

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    host = entry.data[CONF_IP]
    port = entry.data[CONF_PORT]
    device_info = entry.data[CONF_DEVICE_INFO]
    hubkey = gen_hub_key(deviceModel=device_info.get("deviceModel"), deviceRevision=device_info.get("deviceRevision"), serialNumber=device_info.get("serialNumber"))
    hub: TesiraHub = hass.data[DOMAIN]["hubs"][hubkey]

    async_add_entities([TesiraNetConnBinarySensor(hub, hubkey, host, port, device_info)])

class TesiraNetConnBinarySensor(BinarySensorEntity):
    """Binary sensor for Tesira connection status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_should_poll = True

    def __init__(self, hub: TesiraHub, hubkey: str, host: str, port: int, device_info: dict) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._host = host
        self._port = port
        self._device_info = device_info
        self._attr_name = f"Tesira Network Connection Status - {hub.host}:{hub.port} ({device_info.get('serialNumber')})"
        self._attr_unique_id = f"tesira_ttp_{host}_{port}_{device_info.get('serialNumber')}_netconnstate".lower()
        self._attr_is_on = False

    @property
    def is_on(self) -> bool | None:
            return self._attr_is_on

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hubkey)}}

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
        self._attr_is_on = await self._async_ping(self._host)
