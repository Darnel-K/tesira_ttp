# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\tesira_client\client.py                                                      #
# Repository: tesira_ttp                                                                                               #
# Created Date: Friday, July 10th 2026, 1:05:48 AM                                                                     #
# Last Modified: Tuesday, July 14th 2026, 11:33:42 PM                                                                  #
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
import ctypes
import importlib
import sys
import types
import json
import random
import re
import time
import logging
import inspect

_LOGGER = logging.getLogger(__name__)

_ASYNCSSH_MODULE = None
_ASYNCSSH_IMPORT_ERROR = None
_TELNETLIB3_MODULE = None


async def _get_asyncssh():
    global _ASYNCSSH_MODULE, _ASYNCSSH_IMPORT_ERROR

    if _ASYNCSSH_MODULE is not None:
        return _ASYNCSSH_MODULE

    if _ASYNCSSH_IMPORT_ERROR is not None:
        raise ImportError(f"asyncssh import previously failed: {_ASYNCSSH_IMPORT_ERROR}")

    # Python 3.14 compatibility for asyncssh -> fido2 Windows import path.
    if not hasattr(ctypes, "HRESULT"):
        ctypes.HRESULT = ctypes.c_long

    try:
        _ASYNCSSH_MODULE = await asyncio.to_thread(importlib.import_module, "asyncssh")
    except Exception as err:
        err_text = str(err)

        # Some Python 3.14 environments hit fido2's Windows bindings import
        # path on non-Windows platforms (ctypes lacks WinDLL/HRESULT). Provide
        # a minimal stub so asyncssh can import without Windows FIDO support.
        if (
            isinstance(err, AttributeError)
            and ("WinDLL" in err_text or "HRESULT" in err_text)
            and "fido2.client.windows" not in sys.modules
        ):
            win_mod = types.ModuleType("fido2.client.windows")

            class WindowsClient:  # pragma: no cover - compatibility shim only
                @staticmethod
                def is_available() -> bool:
                    return False

            win_mod.WindowsClient = WindowsClient
            sys.modules["fido2.client.windows"] = win_mod

            try:
                _ASYNCSSH_MODULE = await asyncio.to_thread(importlib.import_module, "asyncssh")
            except Exception as retry_err:
                _ASYNCSSH_IMPORT_ERROR = retry_err
                raise
            return _ASYNCSSH_MODULE

        _ASYNCSSH_IMPORT_ERROR = err
        raise

    return _ASYNCSSH_MODULE


async def _get_telnetlib3():
    global _TELNETLIB3_MODULE

    if _TELNETLIB3_MODULE is None:
        _TELNETLIB3_MODULE = await asyncio.to_thread(importlib.import_module, "telnetlib3")

    return _TELNETLIB3_MODULE


# Tesira client (SSH + Telnet).
class TesiraClient:
    """Tesira transport client supporting SSH and Telnet."""

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
        safe_mode=True,
    ):
        # Validate protocol and apply default ports.
        proto = proto.lower().strip()
        if proto not in self.ALLOWED_PROTOCOLS:
            raise self.ProtocolError(f"Unsupported protocol '{proto}'. Allowed: {self.ALLOWED_PROTOCOLS}")

        if proto == "telnet":
            if username != "default" or (password not in ("", None)):
                raise self.AuthenticationUnsupportedError("Telnet only supports user='default' with blank password.")
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

        self._telnet_reader_future = None

        # Internal connection objects
        self._conn = None  # SSH connection OR sentinel True for telnet
        self._chan = None  # SSH channel
        self._session = None  # Session handler
        self._reader = None  # Telnet reader
        self._writer = None  # Telnet writer

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
        self._ssh_session_cls = None

    # Telnet session internals.
    class _TelnetSession:
        def __init__(self, parent):
            self.parent = parent
            self.buffer = ""
            self.complete = asyncio.Event()

            # Track response framing and the last receive timestamp.
            self.ok_seen = False
            self._last_rx = asyncio.get_event_loop().time()

        def data_received(self, data, datatype=None):
            if not data:
                return

            self.buffer += data
            self._last_rx = asyncio.get_event_loop().time()

            _LOGGER.debug("[RX/TELNET] %s", repr(data))

            if "+OK" in data or "-ERR" in data:
                self.ok_seen = True
                self.complete.set()

            for line in data.splitlines():
                if line.strip().startswith("! "):
                    self.parent._handle_publish_event(line.strip())

        def connection_lost(self, exc):
            _LOGGER.warning("[TELNET] Connection lost.")
            self.complete.set()

    # SSH session internals.
    class _SSHSessionBase:
        def __init__(self, parent):
            self.parent = parent
            self.buffer = ""
            self.complete = asyncio.Event()

            # Track response framing and the last receive timestamp.
            self.ok_seen = False
            self._last_rx = asyncio.get_event_loop().time()

        def data_received(self, data, datatype):
            if not data:
                return

            self.buffer += data
            self._last_rx = asyncio.get_event_loop().time()

            _LOGGER.debug("[RX/SSH] %s", repr(data))

            # Mark response start when a status token appears.
            if "+OK" in data or "-ERR" in data:
                self.ok_seen = True
                self.complete.set()

            # Route subscription publish events.
            for line in data.splitlines():
                if line.strip().startswith("! "):
                    self.parent._handle_publish_event(line.strip())

        def connection_lost(self, exc):
            _LOGGER.warning("[SSH] Connection lost")
            self.complete.set()

    # Background Telnet reader.
    async def _telnet_reader_task(self):
        try:
            async for data in self._reader:
                if data == "" or data is None:
                    _LOGGER.debug("[TELNET] EOF received; stopping reader task")
                    break
                self._session.data_received(data)
        except asyncio.CancelledError:
            _LOGGER.debug("[TELNET] Reader task cancelled")
        except Exception as e:
            _LOGGER.error("[TELNET] Reader task crashed: %s", e)

    # Connect via SSH or Telnet with retry/backoff.
    async def connect(self, max_retries=5):
        if self._conn:
            return

        attempt = 1

        for attempt in range(attempt, max_retries + 1):
            backoff = min(1 * (2 ** (attempt - 1)), 20)

            try:
                _LOGGER.debug("[NET] Connecting via %s to %s:%s", self.proto.upper(), self.host, self.port)

                # Open SSH transport.
                if self.proto == "ssh":
                    asyncssh = await _get_asyncssh()

                    if self._ssh_session_cls is None:

                        class _RuntimeSSHSession(asyncssh.SSHClientSession, TesiraClient._SSHSessionBase):
                            def __init__(self, parent):
                                asyncssh.SSHClientSession.__init__(self)
                                TesiraClient._SSHSessionBase.__init__(self, parent)

                            def data_received(self, data, datatype):
                                TesiraClient._SSHSessionBase.data_received(self, data, datatype)

                            def connection_lost(self, exc):
                                TesiraClient._SSHSessionBase.connection_lost(self, exc)

                        self._ssh_session_cls = _RuntimeSSHSession

                    self._conn = await asyncssh.connect(
                        self.host,
                        username=self.username,
                        password=self.password,
                        port=self.port,
                        known_hosts=self.known_hosts,
                    )

                    # Create a fresh session and keep a reference to it.
                    def factory():
                        sess = self._ssh_session_cls(self)
                        self._session = sess
                        return sess

                    self._chan, _ = await self._conn.create_session(factory, term_type="vt100")
                    self._chan.write("\r\n")

                # Open Telnet transport.
                else:
                    telnetlib3 = await _get_telnetlib3()

                    self._reader, self._writer = await telnetlib3.open_connection(
                        self.host,
                        self.port,
                        shell=None,
                    )

                    self._session = TesiraClient._TelnetSession(self)
                    self._conn = True  # Sentinel indicating an active Telnet session.

                    # Run Telnet reads in the background.
                    self._telnet_reader_future = asyncio.create_task(self._telnet_reader_task())

                    self._writer.write("\r\n")

                _LOGGER.debug("[NET] Connected")

                # Start heartbeat once per active connection lifecycle.
                if self._heartbeat_task is None:
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                await self._resubscribe_all()

                break
            except Exception as e:
                if self.proto == "ssh":
                    try:
                        asyncssh = await _get_asyncssh()
                        if isinstance(e, asyncssh.PermissionDenied):
                            _LOGGER.error("[NET] Invalid credentials: %s", e)
                            raise self.InvalidCredentials(f"Invalid credentials: {e}")
                    except ImportError:
                        pass

                _LOGGER.error("[NET] Connection attempt (%s) failed (%s), retrying in %s s", attempt, e, backoff)
                if attempt == max_retries:
                    _LOGGER.error(f"[NET] Maximum connection attempts reached: {e}")
                    raise ConnectionError(f"Maximum connection attempts reached: {e}")
                await asyncio.sleep(backoff)

    # Close active transport and stop heartbeat.
    async def disconnect(self):
        if self._telnet_reader_future:
            self._telnet_reader_future.cancel()
            self._telnet_reader_future = None

        if self.proto == "ssh":
            if self._conn:
                try:
                    self._conn.close()
                    await self._conn.wait_closed()
                except Exception:
                    pass
        else:
            if self._writer:
                try:
                    self._writer.close()
                except Exception:
                    pass

        self._conn = None

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    # Write raw text to the active transport.
    async def _send(self, text: str):
        if self.proto == "ssh":
            self._chan.write(text)
        else:
            self._writer.write(text)

    # Run a command and parse the final +OK/-ERR response token.
    async def command(self, cmd: str, timeout: float = 5.0):
        async with self._lock:
            await self.connect()

            # Reset session state before issuing the command.
            self._session.buffer = ""
            self._session.complete.clear()
            self._session.ok_seen = False
            self._session._last_rx = asyncio.get_event_loop().time()

            _LOGGER.debug("[TX] %s", cmd)

            await self._send(cmd + "\r\n")

            # Wait until a response token (+OK/-ERR) is observed.
            try:
                await asyncio.wait_for(self._session.complete.wait(), timeout)
            except asyncio.TimeoutError:
                raise self.TimeoutError("Timeout waiting for +OK or -ERR", raw=self._session.buffer, cmd=cmd)

            # Add a short tail wait so fragmented payloads can finish arriving.
            idle_grace = 0.15  # seconds; suitable for multi-kB responses

            while True:
                await asyncio.sleep(idle_grace)
                now = asyncio.get_event_loop().time()
                if now - self._session._last_rx >= idle_grace:
                    break
            raw = self._session.buffer.strip()
            lines = [l.strip() for l in raw.splitlines()]

            final = next((l for l in lines if l.startswith("+OK") or l.startswith("-ERR")), None)

            if not final:
                raise self.CommandError("No +OK/-ERR returned", raw=raw, cmd=cmd)

            if final.startswith("-ERR"):
                if self.safe_mode:
                    return {"status": "ERR", "error": final, "raw": raw}
                raise self.CommandError(final, raw=raw, cmd=cmd)

            return final

    # Parse a Tesira +OK payload into JSON-like data.
    async def json(self, cmd: str):
        raw = await self.command(cmd)

        if isinstance(raw, dict):
            return raw

        raw_payload = raw[3:].strip()

        # Fix Tesira arrays
        def fix_array(m):
            parts = m.group(1).split()
            return "[" + ", ".join(parts) + "]"

        raw_payload = re.sub(r"\[([^\[\]]+)\]", fix_array, raw_payload)

        # Insert commas between values and the next quoted key
        raw_payload = re.sub(r'([A-Za-z0-9_"\}\]])\s+"', r'\1, "', raw_payload)

        # Insert commas between quoted fields
        raw_payload = re.sub(r'"\s+"', '", "', raw_payload)

        # Wrap in object if required
        if not raw_payload.startswith("{"):
            raw_payload = "{" + raw_payload + "}"

        # Quote unquoted enum literals
        raw_payload = re.sub(r':([A-Z_][A-Z0-9_]*)\b(?!")', r':"\1"', raw_payload)

        try:
            payload = json.loads(raw_payload)
            if raw.startswith("+OK"):
                payload.setdefault("status", "OK")
            return payload
        except Exception as e:
            raise self.JSONParseError(f"JSON parsing failed: {e}", raw=raw_payload, cmd=cmd)

    # Periodic health check that disconnects after repeated failures.
    async def _heartbeat_loop(self):
        while True:
            interval = self._heartbeat_interval + random.uniform(-self._heartbeat_jitter, self._heartbeat_jitter)
            interval = max(1, interval)

            await asyncio.sleep(interval)

            try:
                await self.command("DEVICE get deviceInfo", timeout=3)
                self._heartbeat_failures = 0
            except Exception as e:
                self._heartbeat_failures += 1
                _LOGGER.warning("Heartbeat failure %s: %s", self._heartbeat_failures, e)

                if self._heartbeat_failures >= self._heartbeat_failure_threshold:
                    await self.disconnect()

    # Subscription helpers.
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
        except self.CommandError:
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

    # Route publish events to token and global callbacks.
    def _handle_publish_event(self, line: str):
        pairs = re.findall(r'"(\w+)":"?([^"\s]+)"?', line)

        data = {}
        for key, value in pairs:
            try:
                data[key] = float(value) if "." in value else int(value)
            except Exception:
                data[key] = value

        token = data.get("publishToken")
        if not token:
            return

        # Subscription callback
        sub = self._subscriptions.get(token)
        if sub:
            cb = sub["callback"]
            try:
                if inspect.iscoroutinefunction(cb):
                    asyncio.create_task(cb(data))
                else:
                    cb(data)
            except Exception as e:
                _LOGGER.error("[EVENT ERROR] %s", e)

        # Global event callback
        if self._event_callback:
            cb = self._event_callback
            try:
                if inspect.iscoroutinefunction(cb):
                    asyncio.create_task(cb(data))
                else:
                    cb(data)
            except Exception as e:
                _LOGGER.error("[EVENT ERROR global] %s", e)

    # Helper methods.
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

    # Custom exception types.
    class CommandError(Exception):
        """Represents a Tesira TTP -ERR response."""

        def __init__(self, message, raw=None, cmd=None):
            super().__init__(message)
            self.message = message
            self.raw = raw
            self.cmd = cmd

    class InvalidCredentials(Exception):
        pass

    class ProtocolError(Exception):
        pass

    class JSONParseError(Exception):
        def __init__(self, message, raw=None, cmd=None):
            super().__init__(message)
            self.message = message
            self.raw = raw
            self.cmd = cmd

    class AuthenticationUnsupportedError(Exception):
        pass

    class TimeoutError(Exception):
        def __init__(self, message, raw=None, cmd=None):
            super().__init__(message)
            self.message = message
            self.raw = raw
            self.cmd = cmd
