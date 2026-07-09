# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\sensor.py                                                                    #
# Repository: tesira_ttp                                                                                               #
# Created Date: Friday, July 10th 2026, 12:12:28 AM                                                                    #
# Last Modified: Friday, July 10th 2026, 12:41:51 AM                                                                   #
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
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, DICT_KEYS, DEFAULTS
from .hub import TesiraHub
from .util import _coerce_bool


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up Tesira sensor entities for a config entry."""

    hubkey = entry.entry_id
    hub: TesiraHub = hass.data[DOMAIN][DICT_KEYS["DATA_HUBS"]][hubkey]
    # devices = copy.deepcopy(entry.data.get(DICT_KEYS["DEVICES"], DEFAULTS["DEVICES"]))
    entities = copy.deepcopy(entry.options.get(DICT_KEYS["ENTITIES"], DEFAULTS["ENTITIES"]))
    entities_list = []

    # Build entities from the dynamic options structure by block type.
    for entity in entities:
        if "sensor" in entity[DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]]:
            match entity[DICT_KEYS["ENTITY_BLOCK_TYPE"]]:
                case "audio_meter":
                    entities_list.append(TesiraAudioMeterBlockLevel(hub=hub, hubkey=hubkey, entity=entity))
                case _:
                    _LOGGER.debug(
                        "Unsupported switch block type '%s' for entity: %s",
                        entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"]),
                        entity,
                    )


    # Remove stale switch entities no longer present in the current config.
    entity_registry = er.async_get(hass)
    expected_ids = {e.unique_id for e in entities_list}
    for entity_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity_entry.domain == "sensor" and entity_entry.unique_id not in expected_ids:
            entity_registry.async_remove(entity_entry.entity_id)

    async_add_entities(entities_list, update_before_add=True)

class TesiraAudioMeterBlockLevel(SensorEntity):
    """Expose a Tesira audio meter block (Level) as a Home Assistant switch entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._sub = entity.get(DICT_KEYS["ENTITY_BLOCK_SUBSCRIBE"])
        self._attr_name = f"Tesira Audio Meter Block - Tag:{self._instance_tag} - Attr:Level - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_level_{self._channel}".lower()
        self._attr_device_class = SensorDeviceClass.SOUND_PRESSURE
        self._attr_native_unit_of_measurement = "dB"
        self._attr_suggested_display_precision = 2
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
        level = data.get("value")
        if level is not None:
            self._attr_native_value = level
            self._attr_available = True
            self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        else:
            _LOGGER.warning("Received subscription update without state value: %s", data)

    async def async_added_to_hass(self) -> None:
        self._hass = self.hass
        if self._sub:
            # Prime state once before starting subscriptions to avoid an empty initial UI state.
            await self.async_update()
            await self._hub.subscribe(self._instance_tag, "level", self._channel, f"hass_sensor_audio_meter_level_{self._instance_tag}_{self._channel}", 100, self._update_state_from_sub)

    async def async_will_remove_from_hass(self) -> None:
        if self._sub:
            await self._hub.unsubscribe(f"hass_sensor_audio_meter_level_{self._instance_tag}_{self._channel}")

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get level {self._channel}")
            level = resp["value"]
            if level is not None:
                self._attr_native_value = level
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse state from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False
