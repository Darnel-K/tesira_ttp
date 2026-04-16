# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\hub.py                                                                       #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Thursday, April 16th 2026, 11:20:15 PM                                                                #
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

import asyncio
import logging

from .tesira_client import TesiraClient
from .const import DEFAULTS

_LOGGER = logging.getLogger(__name__)

class TesiraHub:
    """Shared SSH / Telnet client per host:port."""

    def __init__(self,
        host: str,
        username: str = DEFAULTS["USER"],
        password: str = DEFAULTS["PASS"],
        port: int = DEFAULTS["PORT"],
        proto: str = DEFAULTS["PROTO"],
        known_hosts=None,
        heartbeat_interval: float = 10.0,
        heartbeat_failure_threshold: int = 3,
        heartbeat_jitter: float = 1.5,
        safe_mode=False
        ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.proto = proto
        self.known_hosts = known_hosts
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_failure_threshold = heartbeat_failure_threshold
        self.heartbeat_jitter = heartbeat_jitter
        self.safe_mode = safe_mode
        self.client = TesiraClient(
            host=host,
            port=port,
            username=username,
            password=password,
            proto=proto,
            known_hosts=known_hosts,
            heartbeat_interval=heartbeat_interval,
            heartbeat_failure_threshold=heartbeat_failure_threshold,
            heartbeat_jitter=heartbeat_jitter,
            safe_mode=safe_mode
        )
        # Serialize I/O to avoid interleaving command and subscription operations.
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        # TesiraClient sets _conn when a transport session is active.
        if self.client._conn is not None:
            return True
        else:
            return False

    async def json(self, cmd: str):
        async with self._lock:
            return await self.client.json(cmd)

    async def command(self, cmd: str, timeout=5.0):
        async with self._lock:
            return await self.client.command(cmd, timeout=timeout)

    async def disconnect(self):
        async with self._lock:
            await self.client.disconnect()

    async def subscribe(self, object_type, attribute, index, token, interval_ms, callback):
        async with self._lock:
            await self.client.subscribe(object_type, attribute, index, token, interval_ms, callback)

    async def unsubscribe(self, token: str):
        async with self._lock:
            await self.client.unsubscribe(token)
