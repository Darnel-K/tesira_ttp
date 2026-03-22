# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\tesira_client.py                                                             #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Sunday, March 22nd 2026, 6:53:52 PM                                                                   #
# Original Author: Darnel Kumar                                                                                        #
# Author Github: https://github.com/Darnel-K                                                                           #
#                                                                                                                      #
# This code complies with: https://gist.github.com/Darnel-K/8badda0cabdabb15359350f7af911c90                           #
# Copyright (c) 2026 Darnel Kumar                                                                                      #
# #################################################################################################################### #
from __future__ import annotations

import asyncio
import asyncssh
import telnetlib3
import json
import random
import re
import time
import logging

# For backward compatibility, this module still contains the old TesiraTtpClient class,
# but it is now a wrapper around the new TesiraClient which supports both SSH and Telnet. The new TesiraClient is more robust and feature-rich, while TesiraTtpClient preserves the old API for existing code. New code should use TesiraClient directly for better performance and reliability.
from typing import Optional

_LOGGER = logging.getLogger(__name__)

# =====================================================================
# Legacy Parser Helper Functions (module-level for imports)
# =====================================================================
def parse_first_float(text: str) -> Optional[float]:
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

# =====================================================================
# Exceptions
# =====================================================================
class TesiraError(Exception):
    """Represents a Tesira TTP -ERR response."""
    def __init__(self, message, raw=None, cmd=None):
        super().__init__(message)
        self.message = message
        self.raw = raw
        self.cmd = cmd


class TesiraConnectionError(Exception):
    pass


# =====================================================================
# Tesira Client (SSH + TELNET)
# =====================================================================
class TesiraClient:
    END_TOKENS = ["+OK", "-ERR"]
    ALLOWED_PROTOCOLS = {"ssh", "telnet"}

    def __init__(
        self,
        host: str,
        username: str = "default",
        password: str = "",
        port: int = None,
        proto: str = "ssh",
        known_hosts=None,

        heartbeat_interval: float = 10.0,
        heartbeat_failure_threshold: int = 3,
        heartbeat_jitter: float = 1.5,

        safe_mode=False,
    ):
        # -----------------------------------------------------------------
        # Protocol validation
        # -----------------------------------------------------------------
        proto = proto.lower().strip()
        if proto not in self.ALLOWED_PROTOCOLS:
            raise ValueError(f"Unsupported protocol '{proto}'. Allowed: {self.ALLOWED_PROTOCOLS}")

        if proto == "telnet":
            if username != "default" or (password not in ("", None)):
                raise ValueError("Telnet only supports user='default' with blank password.")
            if port is None:
                port = 23

        if proto == "ssh":
            if port is None:
                port = 22

        self.proto = proto
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.known_hosts = known_hosts

        self.safe_mode = safe_mode

        # Internal connection objects
        self._conn = None        # SSH connection OR sentinel True for telnet
        self._chan = None        # SSH channel
        self._session = None     # Session handler
        self._reader = None      # Telnet reader
        self._writer = None      # Telnet writer

        self._lock = asyncio.Lock()

        # Heartbeat
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_failure_threshold = heartbeat_failure_threshold
        self._heartbeat_jitter = heartbeat_jitter
        self._heartbeat_failures = 0
        self._heartbeat_task = None

        # Cache
        self._device_info_cache = None
        self._device_info_last_updated = 0
        self._device_info_cache_ttl = 60

        # Subscription system
        self._subscriptions = {}
        self._event_callback = None


    # =====================================================================
    # INTERNAL TELNET SESSION
    # =====================================================================
    class _TelnetSession:
        def __init__(self, parent):
            self.parent = parent
            self.buffer = ""
            self.complete = asyncio.Event()

        def data_received(self, data, datatype=None):
            self.buffer += data

            _LOGGER.debug("[RX/TELNET] %s", repr(data))

            # Detect +OK or -ERR
            if "+OK" in self.buffer or "-ERR" in self.buffer:
                self.complete.set()

            # Publish-token events
            for line in self.buffer.splitlines():
                if line.strip().startswith("! "):
                    self.parent._handle_publish_event(line.strip())

        def connection_lost(self, exc):
            _LOGGER.warning("[TELNET] Connection lost.")
            self.complete.set()


    # =====================================================================
    # INTERNAL SSH SESSION
    # =====================================================================
    class _SSHSession(asyncssh.SSHClientSession):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            self.buffer = ""
            self.complete = asyncio.Event()

        def data_received(self, data, datatype):
            self.buffer += data

            _LOGGER.debug("[RX/SSH] %s", repr(data))

            if "+OK" in self.buffer or "-ERR" in self.buffer:
                self.complete.set()

            for line in data.splitlines():
                if line.strip().startswith("! "):
                    self.parent._handle_publish_event(line.strip())

        def connection_lost(self, exc):
            _LOGGER.warning("[SSH] Connection lost")
            self.complete.set()


    # =====================================================================
    # TELNET READER TASK
    # =====================================================================
    async def _telnet_reader_task(self):
        async for data in self._reader:
            self._session.data_received(data)


    # =====================================================================
    # CONNECT (SSH + TELNET)
    # =====================================================================
    async def connect(self, attempt=1):
        if self._conn:
            return

        backoff = min(1 * (2 ** (attempt - 1)), 20)

        try:
            _LOGGER.debug("[NET] Connecting via %s to %s:%s",
                          self.proto.upper(), self.host, self.port)

            # ---------------------------------------------------------
            # SSH CONNECTION
            # ---------------------------------------------------------
            if self.proto == "ssh":

                self._conn = await asyncssh.connect(
                    self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    known_hosts=self.known_hosts,
                )

                # Factory creates NEW session instance and stores it
                def factory():
                    sess = TesiraClient._SSHSession(self)
                    self._session = sess
                    return sess

                self._chan, _ = await self._conn.create_session(factory, term_type="vt100")
                self._chan.write("\r\n")

            # ---------------------------------------------------------
            # TELNET CONNECTION
            # ---------------------------------------------------------
            else:
                self._reader, self._writer = await telnetlib3.open_connection(
                    self.host,
                    self.port,
                    shell=None
                )

                self._session = TesiraClient._TelnetSession(self)
                self._conn = True  # sentinel indicating connected

                # Background reader
                asyncio.create_task(self._telnet_reader_task())

                self._writer.write("\r\n")

            _LOGGER.debug("[NET] Connected")

            # Start heartbeat once
            if self._heartbeat_task is None:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            await self._resubscribe_all()

        except Exception as e:
            _LOGGER.error("[NET] Connect failed (%s), retrying in %s s", e, backoff)
            await asyncio.sleep(backoff)
            return await self.connect(attempt + 1)


    # =====================================================================
    # DISCONNECT
    # =====================================================================
    async def disconnect(self):
        if self.proto == "ssh":
            if self._conn:
                try:
                    self._conn.close()
                    await self._conn.wait_closed()
                except:
                    pass
        else:
            if self._writer:
                try:
                    self._writer.close()
                except:
                    pass

        self._conn = None

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None


    # =====================================================================
    # INTERNAL SEND
    # =====================================================================
    async def _send(self, text: str):
        if self.proto == "ssh":
            self._chan.write(text)
        else:
            self._writer.write(text)


    # =====================================================================
    # COMMAND ENGINE (SSH + TELNET, fragmentation safe)
    # =====================================================================
    async def command(self, cmd: str, timeout=5.0):
        async with self._lock:
            await self.connect()

            # reset
            self._session.buffer = ""
            self._session.complete.clear()

            _LOGGER.debug("[TX] %s", cmd)

            await self._send(cmd + "\r\n")

            try:
                await asyncio.wait_for(self._session.complete.wait(), timeout)
            except asyncio.TimeoutError:
                raise TesiraError("Timeout waiting for +OK or -ERR", raw=self._session.buffer, cmd=cmd)

            raw = self._session.buffer.strip()
            lines = [l.strip() for l in raw.splitlines()]

            final = next((l for l in lines if l.startswith("+OK") or l.startswith("-ERR")), None)

            if not final:
                raise TesiraError("No +OK/-ERR returned", raw=raw, cmd=cmd)

            if final.startswith("-ERR"):
                if self.safe_mode:
                    return {"error": final, "raw": raw}
                raise TesiraError(final, raw=raw, cmd=cmd)

            return final


    # =====================================================================
    # JSON PARSER
    # =====================================================================
    async def json(self, cmd: str):
        raw = await self.command(cmd)

        if isinstance(raw, dict):
            return raw

        payload = raw[3:].strip()

        # Fix Tesira arrays
        def fix_array(m):
            parts = m.group(1).split()
            return "[" + ", ".join(parts) + "]"

        payload = re.sub(r"\[([^\[\]]+)\]", fix_array, payload)

        # Insert commas
        payload = re.sub(r'"\s+"', '", "', payload)

        if not payload.startswith("{"):
            payload = "{" + payload + "}"

        try:
            return json.loads(payload)
        except Exception as e:
            raise TesiraError(f"JSON parsing failed: {e}", raw=payload, cmd=cmd)


    # =====================================================================
    # HEARTBEAT LOOP
    # =====================================================================
    async def _heartbeat_loop(self):
        while True:
            interval = self._heartbeat_interval + random.uniform(
                -self._heartbeat_jitter, self._heartbeat_jitter
            )
            interval = max(1, interval)

            await asyncio.sleep(interval)

            try:
                await self.command("DEVICE get deviceInfo", timeout=3)
                self._heartbeat_failures = 0
            except Exception as e:
                self._heartbeat_failures += 1
                _LOGGER.warning("Heartbeat failure %s: %s",
                                self._heartbeat_failures, e)

                if self._heartbeat_failures >= self._heartbeat_failure_threshold:
                    await self.disconnect()


    # =====================================================================
    # SUBSCRIBE API
    # =====================================================================
    async def subscribe(self, object_type, attribute, index, token, interval_ms, callback):
        cmd = f"{object_type} subscribe {attribute} {index} {token} {interval_ms}"
        await self.command(cmd)

        self._subscriptions[token] = {
            "object_type": object_type,
            "attribute": attribute,
            "index": index,
            "interval_ms": interval_ms,
            "callback": callback,
        }

    async def unsubscribe(self, token: str):
        try:
            await self.command(f"unsubscribe {token}")
        except TesiraError:
            await self.command(f"UNSUBSCRIBE {token}")

        self._subscriptions.pop(token, None)

    async def _resubscribe_all(self):
        for token, sub in self._subscriptions.items():
            cmd = (
                f"{sub['object_type']} subscribe "
                f"{sub['attribute']} "
                f"{sub['index']} "
                f"{token} "
                f"{sub['interval_ms']}"
            )
            try:
                await self.command(cmd)
            except Exception as e:
                _LOGGER.error("[SUB ERROR] %s", e)

    # =====================================================================
    # PUBLISH-EVENT ROUTER
    # =====================================================================
    def _handle_publish_event(self, line: str):
        pairs = re.findall(r'"(\w+)":"?([^"\s]+)"?', line)

        data = {}
        for key, value in pairs:
            try:
                data[key] = float(value) if "." in value else int(value)
            except:
                data[key] = value

        token = data.get("publishToken")
        if not token:
            return

        sub = self._subscriptions.get(token)
        if sub:
            cb = sub["callback"]
            try:
                cb(data)
            except Exception as e:
                _LOGGER.error("[EVENT ERROR] %s", e)

        if self._event_callback:
            try:
                self._event_callback(data)
            except Exception as e:
                _LOGGER.error("[EVENT ERROR global] %s", e)


    # =====================================================================
    # Helpers
    # =====================================================================
    async def ping(self):
        start = time.perf_counter()
        await self.command("DEVICE get deviceInfo")
        end = time.perf_counter()
        return (end - start) * 1000

    def set_quiet(self, quiet: bool):
        self.quiet_mode = quiet

    async def device_info(self, force=False):
        now = time.time()

        if (
            not force
            and self._device_info_cache
            and (now - self._device_info_last_updated) < self._device_info_cache_ttl
        ):
            return self._device_info_cache

        info = await self.json("DEVICE get deviceInfo")
        self._device_info_cache = info
        self._device_info_last_updated = now
        return info

    async def queue(self, cmd: str):
        return await self.command(cmd)


_OK_RE = re.compile(r"\+OK", re.IGNORECASE)
_ERR_RE = re.compile(r"-ERR", re.IGNORECASE)

class TesiraTtpClient:
    """
    Full backwards‑compatible wrapper for the old TesiraTtpClient API.
    Internally uses the new TesiraClient, but preserves:
        - raw output rules
        - CRLF behavior
        - timeout behavior
        - connect()
        - close()
        - send_and_wait()
        - parse helpers
    """

    def __init__(self, ip: str, port: int = 23, proto: str = "telnet",
                 user: str = "default", password: str = None):

        from .tesira_client import TesiraClient

        proto = proto.strip().lower()
        if proto == "telnet":
            _LOGGER.warning(
                "Using Telnet protocol is not recommended. For more information, see https://support.biamp.com/Tesira/Control/Tesira_security_best_practices"
            )
            if user != "default" or password not in (None, ""):
                raise NotImplementedError(
                    "Telnet only supports user='default' + blank password."
                )
        elif proto != "ssh":
            raise ValueError(f"Unsupported proto={proto!r}")

        # Use new TesiraClient internally
        self._client = TesiraClient(
            host=ip,
            username=user,
            password=password or "",
            port=port,
            proto=proto,
        )

        self._lock = asyncio.Lock()
        self._proto = proto
        self._ip = ip
        self._port = port

    # ----------------------------------------------------------------------
    @property
    def is_connected(self) -> bool:
        # old behavior: true if connection exists and not closing
        return self._client._conn is not None

    # ----------------------------------------------------------------------
    async def connect(self) -> None:
        """Old behavior: connect and drain banner."""
        await self._client.connect()

        # OLD CLIENT drained banner for 1 second.
        # We emulate that for backwards compatibility.
        await self._drain_for(1.0)

        # OLD CLIENT nudged prompt readiness with CRLF
        await self._send_raw("\r\n")
        await asyncio.sleep(0.3)  # old timing

    # ----------------------------------------------------------------------
    async def close(self) -> None:
        await self._client.disconnect()

    # ----------------------------------------------------------------------
    async def _send_raw(self, text: str) -> None:
        """Send raw text to Tesira using underlying protocol."""
        if self._proto == "ssh":
            self._client._chan.write(text)
        else:
            self._client._writer.write(text)

    # ----------------------------------------------------------------------
    async def _read_raw(self, max_bytes=1024) -> str:
        """
        Read raw data FROM THE SESSION BUFFER instead of the TelnetReader.
        This avoids telnetlib3 read conflicts.
        """
        if self._proto == "ssh":
            # SSH safe to read directly:
            try:
                return await asyncio.wait_for(self._client._chan.read(max_bytes), timeout=0.2)
            except:
                return ""

        # TELNET SAFE PATH:
        # Pull from buffered data gathered by _telnet_reader_task
        await asyncio.sleep(0.05)  # allow buffer to fill
        buf = self._client._session.buffer
        self._client._session.buffer = ""  # consume it
        return buf


    # ----------------------------------------------------------------------
    async def _drain_for(self, seconds: float) -> str:
        """Old behavior: read whatever arrives for N seconds."""
        end = asyncio.get_running_loop().time() + seconds
        buf = []
        while asyncio.get_running_loop().time() < end:
            chunk = await self._read_raw()
            if chunk:
                buf.append(chunk)
        return "".join(buf)

    # ----------------------------------------------------------------------
    async def send_and_wait(self, line: str, timeout: float = 1.0) -> str:
        """
        EXACT old behavior:
          - sends raw line
          - reads raw text until +OK or -ERR
          - returns the FULL raw blob, not the cleaned line.
        """
        async with self._lock:
            await self.connect()

            # normalize CRLF
            line = line.rstrip("\r\n")
            payload = line + "\r\n"

            await self._send_raw(payload)

            acc = ""
            end = asyncio.get_running_loop().time() + timeout

            while asyncio.get_running_loop().time() < end:
                chunk = await self._read_raw()
                if not chunk:
                    continue
                acc += chunk
                if _OK_RE.search(acc) or _ERR_RE.search(acc):
                    break

            return acc  # return EXACT raw output

    # ----------------------------------------------------------------------
    # Parsing helpers EXACTLY as before
    # ----------------------------------------------------------------------
    @staticmethod
    def parse_first_float(text: str) -> Optional[float]:
        return parse_first_float(text)

    @staticmethod
    def parse_bool(text: str) -> Optional[bool]:
        return parse_bool(text)
