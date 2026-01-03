from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

import telnetlib3

_LOGGER = logging.getLogger(__name__)

_OK_RE = re.compile(r"\+OK", re.IGNORECASE)
_ERR_RE = re.compile(r"-ERR", re.IGNORECASE)

class TesiraTtpClient:
    """Minimal Tesira Text Protocol client over Telnet (TCP/23).

    Keeps one connection and serializes requests with a lock.
    """

    def __init__(self, host: str, port: int = 23) -> None:
        self._host = host
        self._port = port
        self._reader: Optional[telnetlib3.TelnetReader] = None
        self._writer: Optional[telnetlib3.TelnetWriter] = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        if self.is_connected:
            return

        _LOGGER.debug("Connecting Tesira TTP %s:%s", self._host, self._port)
        self._reader, self._writer = await telnetlib3.open_connection(
            self._host,
            self._port,
            shell=None,
            connect_minwait=0.1,
            encoding="utf8",
        )

        # Drain banner / telnet negotiation chatter (best-effort)
        await self._drain_for(1.0)

        # Nudge for prompt readiness
        self._writer.write("\r\n")
        await self._writer.drain()
        await self._drain_for(0.3)

    async def close(self) -> None:
        if self._writer:
            try:
                self._writer.close()
            except Exception:
                pass
        self._reader = None
        self._writer = None

    async def _drain_for(self, seconds: float) -> str:
        """Read whatever arrives for a short time window."""
        if not self._reader:
            return ""
        out: list[str] = []
        end = asyncio.get_running_loop().time() + seconds
        while asyncio.get_running_loop().time() < end:
            try:
                chunk = await asyncio.wait_for(self._reader.read(1024), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            if not chunk:
                break
            out.append(chunk)
        return "".join(out)

    async def send_and_wait(self, line: str, timeout: float = 1.0) -> str:
        """Send one TTP command and return response text up to +OK / -ERR (or timeout)."""
        async with self._lock:
            await self.connect()
            assert self._writer is not None
            assert self._reader is not None

            # Normalize newline -> CRLF
            line = line.rstrip("\r\n")
            payload = line + "\r\n"

            self._writer.write(payload)
            await self._writer.drain()

            acc = ""
            end = asyncio.get_running_loop().time() + timeout
            while asyncio.get_running_loop().time() < end:
                try:
                    chunk = await asyncio.wait_for(self._reader.read(1024), timeout=0.2)
                except asyncio.TimeoutError:
                    continue
                if not chunk:
                    break
                acc += chunk
                if _OK_RE.search(acc) or _ERR_RE.search(acc):
                    break
            return acc

def parse_first_float(text: str) -> Optional[float]:
    """Extract a float from Tesira output (best-effort)."""
    m = re.search(r'"value"\s*:\s*(-?\d+(?:\.\d+)?)', text)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass

    m = re.search(r'(-?\d+(?:\.\d+)?)', text)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass
    return None

def parse_bool(text: str) -> Optional[bool]:
    s = text.lower()
    if "true" in s:
        return True
    if "false" in s:
        return False
    if re.search(r'\b1\b', s):
        return True
    if re.search(r'\b0\b', s):
        return False
    return None
