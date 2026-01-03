from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS, CONF_HOST, CONF_PORT
from .hub import TesiraHub

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
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    hubs: dict[str, TesiraHub] = hass.data[DOMAIN][DATA_HUBS]
    hubkey = f"{host}:{port}"
    hub = hubs.get(hubkey)
    if hub is None:
        hub = TesiraHub(host, port)
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
                await hub.close()
                _LOGGER.debug("Closed Tesira hub for %s", hubkey)

    return unload_ok
