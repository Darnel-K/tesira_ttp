# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\hub.py                                                                       #
# Repository: tesira_ttp                                                                                               #
# Created Date: Sunday, March 22nd 2026, 10:04:37 PM                                                                   #
# Last Modified: Wednesday, March 25th 2026, 10:59:31 PM                                                               #
# Original Author: Darnel Kumar                                                                                        #
# Author Github: https://github.com/Darnel-K                                                                           #
#                                                                                                                      #
# This code complies with: https://gist.github.com/Darnel-K/8badda0cabdabb15359350f7af911c90                           #
# Copyright (c) 2026 Darnel Kumar                                                                                      #
# #################################################################################################################### #
from __future__ import annotations

import asyncio
import logging

from .tesira_client import TesiraClient

_LOGGER = logging.getLogger(__name__)

class TesiraHub:
    """Shared Telnet client per host:port."""

    def __init__(self,
        host: str,
        username: str = "default",
        password: str = "",
        port: int = None,
        proto: str = "ssh",
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
        self._lock = asyncio.Lock()

    @property
    def key(self) -> str:
        return f"{self.host}:{self.port}"

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
