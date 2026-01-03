from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import MediaPlayerEntityFeature, MediaPlayerState
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    CONF_CONTROLS,
    CONF_CONTROL_NAME,
    CONF_INSTANCE_TAG,
    CONF_CHANNEL,
    CONF_MIN_DB,
    CONF_MAX_DB,
    CONF_STEP_DB,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_CONTROL_NAME,
    DEFAULT_CHANNEL,
    DEFAULT_MIN_DB,
    DEFAULT_MAX_DB,
    DEFAULT_STEP_DB,
)
from .hub import TesiraHub
from .tesira_client import parse_bool, parse_first_float

_LOGGER = logging.getLogger(__name__)

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def db_to_level01(db: float, min_db: float, max_db: float) -> float:
    if max_db <= min_db:
        return 0.0
    return clamp((db - min_db) / (max_db - min_db), 0.0, 1.0)

def level01_to_db(level01: float, min_db: float, max_db: float) -> float:
    level01 = clamp(level01, 0.0, 1.0)
    return min_db + level01 * (max_db - min_db)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    # Find shared hub by host:port
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    hubkey = f"{host}:{port}"
    hub: TesiraHub = hass.data[DOMAIN]["hubs"][hubkey]

    controls: list[dict[str, Any]] = list(entry.options.get(CONF_CONTROLS, []))

    entities: list[TesiraVolumeMediaPlayer] = []
    for c in controls:
        name = c.get(CONF_CONTROL_NAME, DEFAULT_CONTROL_NAME)
        tag = c[CONF_INSTANCE_TAG]
        ch = int(c.get(CONF_CHANNEL, DEFAULT_CHANNEL))
        min_db = float(c.get(CONF_MIN_DB, DEFAULT_MIN_DB))
        max_db = float(c.get(CONF_MAX_DB, DEFAULT_MAX_DB))
        step_db = float(c.get(CONF_STEP_DB, DEFAULT_STEP_DB))
        entities.append(TesiraVolumeMediaPlayer(hub, host, port, name, tag, ch, min_db, max_db, step_db))

    async_add_entities(entities, update_before_add=True)

class TesiraVolumeMediaPlayer(MediaPlayerEntity):
    _attr_should_poll = True

    def __init__(
        self,
        hub: TesiraHub,
        host: str,
        port: int,
        name: str,
        instance_tag: str,
        channel: int,
        min_db: float,
        max_db: float,
        step_db: float,
    ) -> None:
        self._hub = hub
        self._host = host
        self._port = port
        self._tag = instance_tag
        self._ch = channel
        self._min_db = min_db
        self._max_db = max_db
        self._step_db = step_db

        self._attr_name = name
        self._attr_unique_id = f"tesira_ttp_{host}_{port}_{self._tag}_{self._ch}".lower()

        self._attr_supported_features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
        )

        self._attr_state = MediaPlayerState.IDLE
        self._attr_available = True

        self._level_db: float | None = None
        self._muted: bool | None = None

    @property
    def volume_level(self) -> float | None:
        if self._level_db is None:
            return None
        return db_to_level01(self._level_db, self._min_db, self._max_db)

    @property
    def is_volume_muted(self) -> bool | None:
        return self._muted

    async def async_update(self) -> None:
        try:
            resp = await self._hub.send_and_wait(f"{self._tag} get level {self._ch}", timeout=2.0)
            level = parse_first_float(resp)
            if level is None:
                raise ValueError(f"Could not parse level from response: {resp!r}")

            self._level_db = float(level)
            self._attr_available = True
            self._attr_state = MediaPlayerState.IDLE

            # mute is best-effort
            try:
                resp_m = await self._hub.send_and_wait(f"{self._tag} get mute {self._ch}", timeout=1.0)
                muted = parse_bool(resp_m)
                if muted is not None:
                    self._muted = muted
            except Exception:
                pass

        except Exception as e:
            _LOGGER.debug("Update failed for %s/%s ch %s: %s", self._host, self._tag, self._ch, e)
            self._attr_available = False
            self._attr_state = MediaPlayerState.UNAVAILABLE

    async def async_set_volume_level(self, volume: float) -> None:
        db = level01_to_db(volume, self._min_db, self._max_db)
        await self._hub.send_and_wait(f"{self._tag} set level {self._ch} {db:.3f}", timeout=2.0)
        self._level_db = db

    async def async_volume_up(self) -> None:
        await self._hub.send_and_wait(
            f"{self._tag} increment level {self._ch} {self._step_db:.3f}",
            timeout=2.0,
        )

    async def async_volume_down(self) -> None:
        await self._hub.send_and_wait(
            f"{self._tag} increment level {self._ch} {-self._step_db:.3f}",
            timeout=2.0,
        )

    async def async_mute_volume(self, mute: bool) -> None:
        resp = await self._hub.send_and_wait(
            f"{self._tag} set mute {self._ch} {'true' if mute else 'false'}",
            timeout=2.0,
        )
        if "-ERR" in resp:
            _LOGGER.warning("Mute command returned error for %s: %s", self.entity_id, resp)
        else:
            self._muted = mute
