# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\button.py                                                                    #
# Repository: tesira_ttp                                                                                               #
# Created Date: Tuesday, July 7th 2026, 11:50:58 PM                                                                    #
# Last Modified: Wednesday, July 8th 2026, 12:17:50 AM                                                                 #
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
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, DICT_KEYS, DEFAULTS
from .hub import TesiraHub


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up Tesira button entities for a config entry."""

    hubkey = entry.entry_id
    hub: TesiraHub = hass.data[DOMAIN][DICT_KEYS["DATA_HUBS"]][hubkey]
    entities = copy.deepcopy(entry.options.get(DICT_KEYS["ENTITIES"], DEFAULTS["ENTITIES"]))
    entities_list = []
    logic_sequence_tags_added: set[str | None] = set()

    # Build entities from the dynamic options structure by block type.
    for entity in entities:
        if "button" in entity[DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]]:
            match entity[DICT_KEYS["ENTITY_BLOCK_TYPE"]]:
                case "logic_pulse":
                    entities_list.append(TesiraLogicPulseBlockStart(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraLogicPulseBlockStop(hub=hub, hubkey=hubkey, entity=entity))
                case "logic_sequence":
                    instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
                    # Sequence start/stop operate on the block as a whole rather than a specific channel.
                    if instance_tag in logic_sequence_tags_added:
                        continue
                    logic_sequence_tags_added.add(instance_tag)
                    entities_list.append(TesiraLogicSequenceBlockStart(hub=hub, hubkey=hubkey, entity=entity))
                    entities_list.append(TesiraLogicSequenceBlockStop(hub=hub, hubkey=hubkey, entity=entity))
                case _:
                    _LOGGER.debug(
                        "Unsupported button block type '%s' for entity: %s",
                        entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"]),
                        entity,
                    )


    # Remove stale button entities no longer present in the current config.
    entity_registry = er.async_get(hass)
    expected_ids = {e.unique_id for e in entities_list}
    for entity_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity_entry.domain == "button" and entity_entry.unique_id not in expected_ids:
            entity_registry.async_remove(entity_entry.entity_id)

    async_add_entities(entities_list, update_before_add=True)

class TesiraLogicPulseBlockStart(ButtonEntity):
    """Expose a Tesira logic pulse block (Start) as a Home Assistant button entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._attr_name = f"Tesira Logic Pulse Block - Tag:{self._instance_tag} - Attr:Start - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_start_{self._channel}".lower()
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_press(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            await self._hub.json(f"{self._instance_tag} startPulse {self._channel}")
        except Exception as e:
            _LOGGER.debug("Button press failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

class TesiraLogicPulseBlockStop(ButtonEntity):
    """Expose a Tesira logic pulse block (Stop) as a Home Assistant button entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._attr_name = f"Tesira Logic Pulse Block - Tag:{self._instance_tag} - Attr:Stop - Chan:{self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_stop_{self._channel}".lower()
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_press(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            await self._hub.json(f"{self._instance_tag} stopPulse {self._channel}")
        except Exception as e:
            _LOGGER.debug("Button press failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

class TesiraLogicSequenceBlockStart(ButtonEntity):
    """Expose a Tesira logic sequence block (Start) as a Home Assistant button entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._attr_name = f"Tesira Logic Sequence Block - Tag:{self._instance_tag} - Attr:Start ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_start".lower()
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_press(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            await self._hub.json(f"{self._instance_tag} startSequence")
        except Exception as e:
            _LOGGER.debug("Button press failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

class TesiraLogicSequenceBlockStop(ButtonEntity):
    """Expose a Tesira logic sequence block (Stop) as a Home Assistant button entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"])
        self._block_type = entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"])
        self._device_id = entity.get(DICT_KEYS["DEVICE_ID"])
        self._channel = int(entity.get(DICT_KEYS["ENTITY_BLOCK_CHANNEL"]))
        self._attr_name = f"Tesira Logic Sequence Block - Tag:{self._instance_tag} - Attr:Stop ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_{self._block_type}_{self._instance_tag}_stop".lower()
        self._attr_available = True

    @property
    def device_info(self):
        return {DICT_KEYS["ENTITY_DEVICE_IDENTIFIERS"]: {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def async_press(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            await self._hub.json(f"{self._instance_tag} stopSequence")
        except Exception as e:
            _LOGGER.debug("Button press failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False
