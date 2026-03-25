from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "tesira_ttp"
PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

CONF_IP = "host"
CONF_PORT = "port"

# Controls live in options as a list of dicts
CONF_CONTROLS = "controls"

CONF_CONTROL_NAME = "name"
CONF_INSTANCE_TAG = "instance_tag"
CONF_CHANNEL = "channel"
CONF_MIN_DB = "min_db"
CONF_MAX_DB = "max_db"
CONF_STEP_DB = "step_db"

DEFAULT_PORT = 23
DEFAULT_CONTROL_NAME = "Tesira Volume"
DEFAULT_CHANNEL = 1
DEFAULT_MIN_DB = -100.0
DEFAULT_MAX_DB = 12.0
DEFAULT_STEP_DB = 0.5
