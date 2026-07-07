# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\binary_sensor.py                                                             #
# Repository: tesira_ttp                                                                                               #
# Created Date: Monday, April 13th 2026, 12:33:01 AM                                                                   #
# Last Modified: Tuesday, July 7th 2026, 11:06:42 PM                                                                   #
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
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, DICT_KEYS, DEFAULTS
from .hub import TesiraHub
from .util import _coerce_bool
from typing import Any

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    hubkey = entry.entry_id
    hub: TesiraHub = hass.data[DOMAIN][DICT_KEYS["DATA_HUBS"]][hubkey]
    devices = copy.deepcopy(entry.data.get(DICT_KEYS["DEVICES"], DEFAULTS["DEVICES"]))
    entities = copy.deepcopy(entry.options.get(DICT_KEYS["ENTITIES"], DEFAULTS["ENTITIES"]))
    entities_list = []

    # Build entities from the dynamic options structure by block type.
    for entity in entities:
        if "binary_sensor" in entity[DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]]:
            match entity[DICT_KEYS["ENTITY_BLOCK_TYPE"]]:
                case "logic_meter":
                    entities_list.append(TesiraLogicMeterBlock(hub=hub, hubkey=hubkey, entity=entity))
                case _:
                    _LOGGER.debug(
                        "Unsupported binary sensor block type '%s' for entity: %s",
                        entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"]),
                        entity,
                    )


    entities_list.append(TesiraHubConnBinarySensor(hub, hubkey))

    for device_id, device in devices[DICT_KEYS["DEVICE_ITEMS"]].items():
        entities_list.append(TesiraNetConnBinarySensor(hub, device_id, device))


    # Remove stale binary_sensor entities no longer present in the current config.
    entity_registry = er.async_get(hass)
    expected_ids = {e.unique_id for e in entities_list}
    for entity_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity_entry.domain == "binary_sensor" and entity_entry.unique_id not in expected_ids:
            entity_registry.async_remove(entity_entry.entity_id)

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
        self._device_info = device.get(DICT_KEYS["DEVICE_INFO"], {})
        self._device_connection_info = device.get(DICT_KEYS["DEVICE_CONNECTION_INFO"], {})
        self._attr_name = f"Network Connection Status ({self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._device_id[:10]}_netconnstate".lower()
        self._attr_is_on = False
        self._attr_available = True

    @property
    def is_on(self) -> bool | None:
            return self._attr_is_on

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}}

    async def _async_ping(self, host: str) -> bool:
        """Ping the host using the OS ping command."""
        # Home Assistant containers use Linux ping flags: one packet, one-second timeout.
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
        # Keep this state independent from protocol connectivity to show host reachability.
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
        # Reflect the client session state managed by TesiraHub/TesiraClient.
        self._attr_is_on = self._hub.is_connected

class TesiraLogicMeterBlock(BinarySensorEntity):
    """Expose a Tesira logic meter block as a Home Assistant binary sensor entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._sub = entity.get(DICT_KEYS["ENTITY_BLOCK_SUBSCRIBE"])
        self._attr_name = f"Tesira Logic Meter Block - Tag:{self._instance_tag} - Attr:State - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_state_{self._channel}".lower()
        self._attr_is_on: bool = False
        self._attr_available = True

        if self._sub:
            # Subscription mode pushes updates from the DSP, so polling is unnecessary.
            self._attr_should_poll = False
        else:
            self._attr_should_poll = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    def _update_state_from_sub(self, data: dict) -> None:
        state = data.get("value")
        if state is not None:
            self._attr_is_on = _coerce_bool(state)
            self._attr_available = True
            self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        else:
            _LOGGER.warning("Received subscription update without state value: %s", data)

    async def async_added_to_hass(self) -> None:
        self._hass = self.hass
        if self._sub:
            # Prime state once before starting subscriptions to avoid an empty initial UI state.
            await self.async_update()
            await self._hub.subscribe(self._instance_tag, "state", self._channel, f"hass_switch_level_meter_{self._instance_tag}_{self._channel}", 100, self._update_state_from_sub)

    async def async_will_remove_from_hass(self) -> None:
        if self._sub:
            await self._hub.unsubscribe(f"hass_switch_level_meter_{self._instance_tag}_{self._channel}")

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get state {self._channel}")
            state = resp["value"]
            if state is not None:
                self._attr_is_on = _coerce_bool(state)
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse state from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

class TesiraLogicPulseBlock(BinarySensorEntity):
    """Expose a Tesira logic pulse block as a Home Assistant binary sensor entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._attr_name = f"Tesira Logic Pulse Block - Tag:{self._instance_tag} - Attr:Active - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_active_{self._channel}".lower()
        self._attr_is_on: bool = False
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get active {self._channel}")
            state = resp["value"]
            if state is not None:
                self._attr_is_on = _coerce_bool(state)
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse active state from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False
