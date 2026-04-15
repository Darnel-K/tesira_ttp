# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\media_player.py                                                              #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Wednesday, April 15th 2026, 12:37:23 AM                                                               #
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
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import MediaPlayerEntityFeature, MediaPlayerState

from .const import DOMAIN, DICT_KEYS, DEFAULTS
from .util import db_to_level, level_to_db
from .hub import TesiraHub


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    hubkey = entry.entry_id
    hub: TesiraHub = hass.data[DOMAIN][DICT_KEYS["DATA_HUBS"]][hubkey]
    # devices = copy.deepcopy(entry.data.get(DICT_KEYS["DEVICES"], DEFAULTS["DEVICES"]))
    entities = copy.deepcopy(entry.options.get(DICT_KEYS["ENTITIES"], DEFAULTS["ENTITIES"]))
    entities_list = []

    # Build entities from the dynamic options structure by block type.
    for block_type, item_list in entities.items():
        for item in item_list:
            if "media_player" in item["supported_entity_types"]:
                 match block_type:
                    case "level":
                         entities_list.append(TesiraLevelBlock(hub=hub, hubkey=hubkey, entity=item))

    async_add_entities(entities_list, update_before_add=True)

    # controls: list[dict[str, Any]] = list(entry.options.get(DICT_KEYS["CONTROLS"], []))

    # entities: list[TesiraVolumeMediaPlayer] = []
    # for c in controls:
    #     name = c.get(DICT_KEYS["CONTROL_NAME"], DEFAULTS["CONTROL_NAME"])
    #     tag = c[DICT_KEYS["INSTANCE_TAG"]]
    #     ch = int(c.get(DICT_KEYS["CHANNEL"], DEFAULTS["CHANNEL"]))
    #     min_db = float(c.get(DICT_KEYS["MIN_DB"], DEFAULTS["MIN_DB"]))
    #     max_db = float(c.get(DICT_KEYS["MAX_DB"], DEFAULTS["MAX_DB"]))
    #     step_db = float(c.get(DICT_KEYS["STEP_DB"], DEFAULTS["STEP_DB"]))
    #     entities.append(TesiraVolumeMediaPlayer(hub, hubkey, name, tag, ch, min_db, max_db, step_db))

    # async_add_entities(entities, update_before_add=True)

class TesiraLevelBlock(MediaPlayerEntity):
    """Expose a Tesira level block channel as a Home Assistant media player volume entity."""

    def __init__(self, hub: TesiraHub, hubkey: str, entity: dict[str, Any]) -> None:
        self._hub = hub
        self._hubkey = hubkey
        self._entity = entity
        self._instance_tag = entity.get("instance_tag")
        self._device_id = entity.get("device")
        self._channel = int(entity.get("channel"))
        self._sub = entity.get("subscribe")
        self._attr_name = f"Tesira Level Block - {self._instance_tag} - Channel {self._channel} ({self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]})"
        self._attr_unique_id = f"tesira_ttp_{self._hubkey[:10] if self._device_id == "None" else self._device_id[:10]}_level_{self._instance_tag}_{self._channel}".lower()
        self._attr_supported_features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
        )
        self._attr_state = MediaPlayerState.IDLE
        self._attr_available = True
        self._max_db: float = 12.0
        self._min_db: float = -100.0
        self._current_level: float | None = None
        self._muted: bool | None = None

        if self._sub:
            # Subscription mode pushes updates from the DSP, so polling is unnecessary.
            self._attr_should_poll = False
        else:
            self._attr_should_poll = True

    @property
    def volume_level(self) -> float | None:
        if self._current_level is None:
            return None
        return db_to_level(self._current_level, self._min_db, self._max_db)

    @property
    def is_volume_muted(self) -> bool | None:
        return self._muted

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._device_id)}} if self._device_id != "None" else None

    async def get_block_details(self) -> None:
        # Pull live min/max dB limits to normalize volume values correctly for this block.
        resp = await self._hub.json(f"{self._instance_tag} get maxLevel {self._channel}")
        self._max_db = float(resp.get("value", 12.0))
        resp = await self._hub.json(f"{self._instance_tag} get minLevel {self._channel}")
        self._min_db = float(resp.get("value", -100.0))

    def _update_level_from_sub(self, data: dict) -> None:
        level = data.get("value")
        if level is not None:
            self._current_level = float(level)
            self._attr_available = True
            self._attr_state = MediaPlayerState.IDLE
            self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        else:
            _LOGGER.warning("Received subscription update without level value: %s", data)

    def _update_mute_from_sub(self, data: dict) -> None:
        muted = data.get("value")
        if muted is not None:
            self._muted = bool(muted)
            self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)
        else:
            _LOGGER.warning("Received subscription update without mute value: %s", data)

    async def async_added_to_hass(self) -> None:
        self._hass = self.hass
        if self._sub:
            # Prime state once before starting subscriptions to avoid an empty initial UI state.
            await self.async_update()
            await self._hub.subscribe(self._instance_tag, "level", self._channel, f"hass_media_player_level_{self._instance_tag}_{self._channel}", 100, self._update_level_from_sub)
            await self._hub.subscribe(self._instance_tag, "mute", self._channel, f"hass_media_player_mute_{self._instance_tag}_{self._channel}", 100, self._update_mute_from_sub)

    async def async_will_remove_from_hass(self) -> None:
        if self._sub:
            await self._hub.unsubscribe(f"hass_media_player_level_{self._instance_tag}_{self._channel}")
            await self._hub.unsubscribe(f"hass_media_player_mute_{self._instance_tag}_{self._channel}")

    async def async_update(self) -> None:
        try:
            # Limits may differ between blocks/channels, so refresh before conversion each cycle.
            await self.get_block_details()
            resp = await self._hub.json(f"{self._instance_tag} get level {self._channel}")
            level = resp["value"]
            if level is not None:
                self._current_level = float(level)
                self._attr_available = True
                self._attr_state = MediaPlayerState.IDLE
            else:
                raise ValueError(f"Could not parse level from response: {resp!r}")

            try:
                resp_m = await self._hub.json(f"{self._instance_tag} get mute {self._channel}")
                muted = resp_m['value']
                if muted is not None:
                    self._muted = bool(muted)
            except Exception:
                pass
        except Exception as e:
            _LOGGER.debug("Update failed for %s: %s", self._attr_unique_id, e)
            self._attr_available = False

    async def async_set_volume_level(self, volume: float) -> None:
        db = level_to_db(volume, self._min_db, self._max_db)
        await self._hub.json(f"{self._instance_tag} set level {self._channel} {db:.3f}")
        self._current_level = db

    async def async_volume_up(self) -> None:
        await self._hub.json(f"{self._instance_tag} increment level {self._channel} 0.1")

    async def async_volume_down(self) -> None:
        await self._hub.json(f"{self._instance_tag} increment level {self._channel} -0.1")

    async def async_mute_volume(self, mute: bool) -> None:
        resp = await self._hub.json(f"{self._instance_tag} set mute {self._channel} {'true' if mute else 'false'}")
        if "error" in resp:
            _LOGGER.warning("Mute command returned error for %s: %s", self._attr_unique_id, resp['error'])
        else:
            self._muted = mute
