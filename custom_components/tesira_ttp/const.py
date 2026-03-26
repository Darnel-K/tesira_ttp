# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\const.py                                                                     #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Thursday, March 26th 2026, 12:26:20 AM                                                                #
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
