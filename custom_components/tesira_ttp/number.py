# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\number.py                                                                    #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, April 16th 2026, 11:44:37 PM                                                                 #
# Last Modified: Tuesday, July 14th 2026, 12:17:57 AM                                                                  #
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
from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, DICT_KEYS, DEFAULTS
from .hub import TesiraHub


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up Tesira number entities for a config entry."""

    hubkey = entry.entry_id
    hub: TesiraHub = hass.data[DOMAIN][DICT_KEYS["DATA_HUBS"]][hubkey]
    entities = copy.deepcopy(entry.options.get(DICT_KEYS["ENTITIES"], DEFAULTS["ENTITIES"]))
    entities_list = []

    # Build entities from the dynamic options structure by block type.
    for entity in entities:
        if "number" in entity[DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]]:
            match entity[DICT_KEYS["ENTITY_BLOCK_TYPE"]]:
                case "logic_delay":
                    entities_list.append(TesiraLogicDelayBlockOnDelay(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraLogicDelayBlockOffDelay(hub=hub, hubkey=hubkey, entity=entity))
                case "logic_pulse":
                    entities_list.append(TesiraLogicPulseBlockOnDuration(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraLogicPulseBlockOffDuration(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraLogicPulseBlockPulseCount(hub=hub, hubkey=hubkey, entity=entity))
                case "logic_sequence":
                    entities_list.append(TesiraLogicSequenceBlockOnDuration(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraLogicSequenceBlockOffDuration(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraLogicSequenceBlockPulseCount(hub=hub, hubkey=hubkey, entity=entity))
                case "audio_meter":
                    entities_list.append(TesiraAudioMeterBlockHoldTime(hub=hub, hubkey=hubkey, entity=entity))
                case "signal_present_meter":
                    entities_list.append(TesiraSignalPresentMeterBlockOffDelay(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraSignalPresentMeterBlockOnDelay(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraSignalPresentMeterBlockThreshold(hub=hub, hubkey=hubkey, entity=entity))
                case _:
                    _LOGGER.debug(
                        "Unsupported number block type '%s' for entity: %s",
                        entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"]),
                        entity,
                    )


    # Remove stale number entities no longer present in the current config.
    entity_registry = er.async_get(hass)
    expected_ids = {e.unique_id for e in entities_list}
    for entity_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity_entry.domain == "number" and entity_entry.unique_id not in expected_ids:
            entity_registry.async_remove(entity_entry.entity_id)

    async_add_entities(entities_list, update_before_add=True)

class TesiraLogicDelayBlockOnDelay(NumberEntity):
    """Expose a Tesira logic delay block (On Delay) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"]))
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"]))
        self._attr_name = f"Tesira Logic Delay Block - Tag:{self._instance_tag} - Attr:OnDelay - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_ondelay_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get onDelayMs {self._channel}")
            delay = resp["value"]
            if delay is not None:
                self._attr_native_value = delay
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse delay from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set onDelayMs {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set delay for %s: %s", self._attr_unique_id, e)

class TesiraLogicDelayBlockOffDelay(NumberEntity):
    """Expose a Tesira logic delay block (Off Delay) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"]))
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"]))
        self._attr_name = f"Tesira Logic Delay Block - Tag:{self._instance_tag} - Attr:OffDelay - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_offdelay_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get offDelayMs {self._channel}")
            delay = resp["value"]
            if delay is not None:
                self._attr_native_value = delay
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse delay from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set offDelayMs {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set delay for %s: %s", self._attr_unique_id, e)

class TesiraLogicPulseBlockOffDuration(NumberEntity):
    """Expose a Tesira logic pulse block (Off Duration) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= 1000 else 1000
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 60000 else 60000
        self._attr_name = f"Tesira Logic Pulse Block - Tag:{self._instance_tag} - Attr:OffDuration - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_offduration_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get durationOff {self._channel}")
            off_duration = resp["value"]
            if off_duration is not None:
                self._attr_native_value = off_duration
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse duration from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set durationOff {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set duration for %s: %s", self._attr_unique_id, e)

class TesiraLogicPulseBlockOnDuration(NumberEntity):
    """Expose a Tesira logic pulse block (On Duration) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= 1000 else 1000
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 60000 else 60000
        self._attr_name = f"Tesira Logic Pulse Block - Tag:{self._instance_tag} - Attr:OnDuration - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_onduration_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get durationOn {self._channel}")
            on_duration = resp["value"]
            if on_duration is not None:
                self._attr_native_value = on_duration
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse duration from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set durationOn {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set duration for %s: %s", self._attr_unique_id, e)

class TesiraLogicPulseBlockPulseCount(NumberEntity):
    """Expose a Tesira logic pulse block (Pulse Count) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= 1 else 1
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 100 else 100
        self._attr_name = f"Tesira Logic Pulse Block - Tag:{self._instance_tag} - Attr:PulseCount - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_pulsecount_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get pulseCount {self._channel}")
            pulse_count = resp["value"]
            if pulse_count is not None:
                self._attr_native_value = pulse_count
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse pulse count from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set pulseCount {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set pulse count for %s: %s", self._attr_unique_id, e)

class TesiraLogicSequenceBlockOffDuration(NumberEntity):
    """Expose a Tesira logic sequence block (Off Duration) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= 500 else 500
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 60000 else 60000
        self._attr_name = f"Tesira Logic Sequence Block - Tag:{self._instance_tag} - Attr:OffDuration - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_offduration_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get durationOff {self._channel}")
            off_duration = resp["value"]
            if off_duration is not None:
                self._attr_native_value = off_duration
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse duration from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set durationOff {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set duration for %s: %s", self._attr_unique_id, e)

class TesiraLogicSequenceBlockOnDuration(NumberEntity):
    """Expose a Tesira logic sequence block (On Duration) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= 500 else 500
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 60000 else 60000
        self._attr_name = f"Tesira Logic Sequence Block - Tag:{self._instance_tag} - Attr:OnDuration - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_onduration_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get durationOn {self._channel}")
            on_duration = resp["value"]
            if on_duration is not None:
                self._attr_native_value = on_duration
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse duration from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set durationOn {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set duration for %s: %s", self._attr_unique_id, e)

class TesiraLogicSequenceBlockPulseCount(NumberEntity):
    """Expose a Tesira logic sequence block (Pulse Count) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= 1 else 1
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 100 else 100
        self._attr_name = f"Tesira Logic Sequence Block - Tag:{self._instance_tag} - Attr:PulseCount - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_pulsecount_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get pulseCount {self._channel}")
            pulse_count = resp["value"]
            if pulse_count is not None:
                self._attr_native_value = pulse_count
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse pulse count from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set pulseCount {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set pulse count for %s: %s", self._attr_unique_id, e)

class TesiraAudioMeterBlockHoldTime(NumberEntity):
    """Expose a Tesira audio meter block (Hold Time) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"]))
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"]))
        self._attr_name = f"Tesira Audio Meter Block - Tag:{self._instance_tag} - Attr:HoldTime - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_holdtime_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get holdTime {self._channel}")
            hold_time = resp["value"]
            if hold_time is not None:
                self._attr_native_value = hold_time
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse hold time from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set holdTime {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set hold time for %s: %s", self._attr_unique_id, e)

class TesiraSignalPresentMeterBlockOffDelay(NumberEntity):
    """Expose a Tesira signal present meter block (Off Delay) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= 0 else 0
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 60000 else 60000
        self._attr_name = f"Tesira Signal Present Meter Block - Tag:{self._instance_tag} - Attr:OffDelay - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_offdelay_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get offDelay {self._channel}")
            delay = resp["value"]
            if delay is not None:
                self._attr_native_value = delay
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse delay from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set offDelay {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set delay for %s: %s", self._attr_unique_id, e)

class TesiraSignalPresentMeterBlockOnDelay(NumberEntity):
    """Expose a Tesira signal present meter block (On Delay) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= 0 else 0
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 60000 else 60000
        self._attr_name = f"Tesira Signal Present Meter Block - Tag:{self._instance_tag} - Attr:OnDelay - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_ondelay_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get onDelay {self._channel}")
            delay = resp["value"]
            if delay is not None:
                self._attr_native_value = delay
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse delay from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set onDelay {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set delay for %s: %s", self._attr_unique_id, e)

class TesiraSignalPresentMeterBlockThreshold(NumberEntity):
    """Expose a Tesira signal present meter block (Threshold) as a Home Assistant number entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._min_value = int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MIN_VALUE"])) >= -64 else -64
        self._max_value = int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) if int(entity.get(DICT_KEYS["ENTITY_MAX_VALUE"])) <= 30 else 30
        self._attr_name = f"Tesira Signal Present Meter Block - Tag:{self._instance_tag} - Attr:Threshold - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_threshold_{self._channel}".lower()
        self._attr_mode = "box"
        self._attr_native_step = 1
        self._attr_native_max_value = self._max_value
        self._attr_native_min_value = self._min_value
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_native_unit_of_measurement = "ms"
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            resp = await self._hub.json(f"{self._instance_tag} get threshold {self._channel}")
            threshold = resp["value"]
            if threshold is not None:
                self._attr_native_value = threshold
                self._attr_available = True
            else:
                raise ValueError(f"Could not parse threshold from response: {resp!r}")
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_native_value(self, value: int) -> None:
        try:
            await self._hub.json(f"{self._instance_tag} set threshold {self._channel} {value}")
            self._attr_is_on = True
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.debug("Failed to set threshold for %s: %s", self._attr_unique_id, e)
