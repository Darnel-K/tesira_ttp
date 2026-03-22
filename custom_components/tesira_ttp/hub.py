from __future__ import annotations

import asyncio
import logging

from .tesira_client import TesiraTtpClient

_LOGGER = logging.getLogger(__name__)

class TesiraHub:
    """Shared Telnet client per ip:port."""

    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.client = TesiraTtpClient(ip, port)
        self._lock = asyncio.Lock()

    @property
    def key(self) -> str:
        return f"{self.ip}:{self.port}"

    async def send_and_wait(self, line: str, timeout: float = 1.0) -> str:
        # TesiraTtpClient already serializes requests, but we guard connect/close too.
        async with self._lock:
            return await self.client.send_and_wait(line, timeout=timeout)

    async def close(self) -> None:
        async with self._lock:
            await self.client.close()
