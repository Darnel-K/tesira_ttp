# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\util.py                                                                      #
# Repository: tesira_ttp                                                                                               #
# Created Date: Saturday, March 28th 2026, 10:45:20 PM                                                                 #
# Last Modified: Sunday, May 3rd 2026, 12:49:07 AM                                                                     #
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
"""Utility helpers for tesira_ttp."""

from __future__ import annotations

from typing import Dict, Any, Awaitable, Callable
from .const import DOMAIN, DICT_KEYS, DEFAULTS, BLOCK_SCHEMA_DATA

import base64
import json
import copy

def _devices(entry: dict[Any, Any]) -> dict[str, Any]:
    """Return a copy of the devices dict from the config entry data, or defaults if not available"""
    if entry is None:
        return copy.deepcopy(DEFAULTS["DEVICES"])

    return copy.deepcopy(entry.data.get(DICT_KEYS["DEVICES"], DEFAULTS["DEVICES"]))

def _credentials(entry: dict[Any, Any], device_id: str | None = None) -> dict[str, Any]:
    """Return a copy of the credentials dict from the config entry data, or defaults if not available"""
    if entry is None:
        return copy.deepcopy(DEFAULTS["CREDENTIALS"])

    credentials = copy.deepcopy(entry.data.get(DICT_KEYS["CREDENTIALS"], DEFAULTS["CREDENTIALS"]))
    if device_id:
        return credentials.get(device_id, DEFAULTS["CREDENTIALS"])
    return credentials

def _entities(entry: dict[Any, Any]) -> list[dict[str, Any]]:
    """Return a copy of the entities list from the config entry options, or defaults if not available"""
    if entry is None:
        return copy.deepcopy(DEFAULTS["ENTITIES"])

    return copy.deepcopy(entry.options.get(DICT_KEYS["ENTITIES"], DEFAULTS["ENTITIES"]))

def _device_name_map(devices: dict[Any, Any]) -> dict[str, str]:
    """Return a mapping of human-readable device names to device IDs."""

    items = devices.get(DICT_KEYS["DEVICE_ITEMS"], {})
    name_map: dict[str, str] = {}
    seen_names: set[str] = set()

    # Map display names to IDs, adding a suffix when names collide.
    for device_id, device in items.items():
        info = device.get(DICT_KEYS["DEVICE_INFO"], {})
        base_name = info.get("name", "Unknown Device")
        serial = info.get("serial_number")

        name = base_name

        # Ensure uniqueness of displayed names
        if name in seen_names:
            suffix = serial or device_id[:8]
            name = f"{base_name} ({suffix})"

        seen_names.add(name)
        name_map[name] = device_id

    return dict(sorted(name_map.items()))

def _entity_name_map(entities: list[dict[str, Any]]) -> dict[str, str]:
    """Return a mapping of human-readable entity names to themselves, for use with cv.multi_select."""

    names: dict[str, str] = {}

    # Map display names to themselves, adding a suffix when names collide.
    for i, entity in enumerate(entities):
        name = f"{entity.get(DICT_KEYS["ENTITY_BLOCK_TYPE"], 'Unknown Block')} - {entity.get(DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], '')}"

        if name in names:
            name = f"{name} ({i})"

        names[name] = name

    return names

def gen_device_dict(host: str, port: int, proto: str, user: str, pwrd: str, device_info: dict, device_id: str = None) -> Dict[str, Any]:
    """
    Generate a dictionary template for a Tesira device.

    Returns:
        A dictionary with the structure for storing device information and connection details.
    """
    if device_id is None:
        device_id = gen_device_id(device_info["deviceModel"], device_info["deviceRevision"], device_info["serialNumber"])
    return {
        DICT_KEYS["DEVICE_CONNECTION_INFO"]: {
            DICT_KEYS["HOST"]: host,
            DICT_KEYS["PORT"]: port,
            DICT_KEYS["PROTO"]: proto
        },
        DICT_KEYS["DEVICE_INFO"]: {
            "name": f"Biamp - {device_info['deviceModel']} - {host}:{port} - ({device_id[:10]})",
            "manufacturer": "Biamp",
            "model": device_info["deviceModel"],
            "model_id": device_info["deviceModel"],
            "sw_version": device_info["firmwareVersion"],
            "hw_version": device_info["deviceRevision"],
            "serial_number": device_info["serialNumber"]
        }
    }

def gen_credential_dict(user: str, pwrd: str) -> dict[str, Any]:
    """
    Generate a dictionary for storing authentication credentials.

    Returns:
        A dictionary with the structure for storing username and password.
    """
    return {
        DICT_KEYS["USER"]: user,
        DICT_KEYS["PASS"]: pwrd
    }

def gen_entity_dict(block_type: str, form_data: dict[str, Any], device_names: dict[str, str]) -> dict[str, Any]:
    """
    Generate a dictionary template for an entity based on its block type and identifying fields.

    Args:
        block_type: The type of the Tesira block (e.g., "level", "switch").
        form_data: A dictionary of field names and their values that identify the entity.

    Returns:
        A dictionary with the structure for storing entity information and metadata.
    """
    entity = {
        DICT_KEYS["ENTITY_BLOCK_TYPE"]: block_type,
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: BLOCK_SCHEMA_DATA[block_type].get(DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"], [])
    }
    fields = BLOCK_SCHEMA_DATA[block_type][DICT_KEYS["ENTITY_BLOCK_FIELDS"]]

    for field in fields:
        # Copy each configured field from the submitted form.
        entity[field] = form_data.get(field)
        if field == DICT_KEYS["DEVICE_ID"] and form_data.get(field) != "None":
            # Persist selected devices by ID instead of display name.
            entity[field] = device_names.get(form_data.get(field))

    return entity

def _redact_device(device: dict[str, Any]) -> dict[str, Any]:
    # Return a copy so logging/debug views never mutate stored config data.
    redacted = copy.deepcopy(device)
    auth = redacted.get(DICT_KEYS["DEVICE_CONNECTION_INFO"], {}).get(DICT_KEYS["DEVICE_CONNECTION_INFO_AUTH"], None)
    if auth is not None:
        auth[DICT_KEYS["USER"]] = "***"
        auth[DICT_KEYS["PASS"]] = "***"
    return redacted


def gen_device_id(deviceModel: str, deviceRevision: int, serialNumber: str, format: str = "b64") -> str:
    """
    Generate a unique key for a Tesira device based on its properties.

    Args:

        deviceModel: The model of the device.
        deviceRevision: The revision of the device.
        serialNumber: The serial number of the device.
        format: The output format of the key ("b64" for base64, "plain" for raw string, "json" for JSON).

    Returns:
        A unique string key representing the device configuration.
    """
    ALLOWED_FORMATS = {"b64", "plain", "json"}
    device_id = {"deviceModel": deviceModel.lower(), "deviceRevision": deviceRevision.lower(), "serialNumber": serialNumber.lower()}
    format = format.lower().strip()
    if format not in ALLOWED_FORMATS:
            raise ValueError(f"Unsupported format '{format}'. Allowed: {ALLOWED_FORMATS}")

    match format:
        case "json":
             return json.dumps(device_id, sort_keys=True)
        case "plain":
             return f"{device_id['deviceModel']}:{device_id['deviceRevision']}:{device_id['serialNumber']}"
        case "b64":
               # URL-safe base64 keeps IDs compact while remaining safe for HA identifiers.
             return base64.urlsafe_b64encode(json.dumps(device_id, sort_keys=True).encode()).decode()

def parse_device_id(device_id: str, format: str = "b64") -> Dict[str, str]:
    """
    Parse a device ID back into its components.

    Args:
        device_id: The unique ID representing the device configuration.
        format: The format of the input ID ("b64" for base64, "plain" for raw string, "json" for JSON).

    Returns:
        A dictionary containing the original parameters (deviceModel, deviceRevision, serialNumber).
    """
    ALLOWED_FORMATS = {"b64", "plain", "json"}
    format = format.lower().strip()
    if format not in ALLOWED_FORMATS:
            raise ValueError(f"Unsupported format '{format}'. Allowed: {ALLOWED_FORMATS}")

    match format:
        case "json":
             return json.loads(device_id)
        case "plain":
             parts = device_id.split(":")
             if len(parts) != 3:
                 raise ValueError("Invalid plain format. Expected 'deviceModel:deviceRevision:serialNumber'")
             return {"deviceModel": parts[0], "deviceRevision": parts[1], "serialNumber": parts[2]}
        case "b64":
               # Input is expected to match gen_device_id(..., format="b64") output.
             decoded = base64.urlsafe_b64decode(device_id.encode()).decode()
             return json.loads(decoded)

def clamp(value: float, minimum: float, maximum: float) -> float:
    """
    Restrict a value to lie within the given minimum and maximum bounds.
    """
    return max(minimum, min(maximum, value))


def _coerce_bool(value: Any) -> bool:
    """Normalize Tesira payload values into a strict boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "on", "1", "yes"}:
            return True
        if normalized in {"false", "off", "0", "no"}:
            return False
    raise ValueError(f"Could not convert value to bool: {value!r}")


def db_to_level(db_value: float, min_db: float, max_db: float) -> float:
    """
    Convert a decibel value into a normalized range [0.0, 1.0].
    """
    if max_db <= min_db:
        return 0.0

    normalized = (db_value - min_db) / (max_db - min_db)
    return clamp(normalized, 0.0, 1.0)


def level_to_db(level: float, min_db: float, max_db: float) -> float:
    """
    Convert a normalized value [0.0, 1.0] back into a decibel value.
    """
    level = clamp(level, 0.0, 1.0)
    return min_db + level * (max_db - min_db)

class TesiraTTPException(Exception):
    """Base exception for tesira_ttp."""
    class NotPermitted(Exception):
        """Raised when an action is not permitted by the integration."""
        pass

class VersionMigrations:
    """Container for config entry migration functions to handle updates to config structure across versions."""

    _Version = tuple[int, int]
    _Edge = tuple[_Version, _Version]
    _MigrationFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]

    @staticmethod
    def _version(major: int, minor: int) -> _Version:
        return (major, minor)

    @classmethod
    def _iter_known_versions(cls, flow_type: str) -> set[_Version]:
        """Collect all known versions from migration method names."""
        versions: set[VersionMigrations._Version] = set()
        prefix_upgrade = f"_{flow_type}_upgrade_"
        prefix_downgrade = f"_{flow_type}_downgrade_"

        for attr_name in dir(cls):
            if attr_name.startswith(prefix_upgrade):
                from_v, to_v = attr_name[len(prefix_upgrade):].split("_to_", 1)
                versions.add(cls._parse_version_token(from_v))
                versions.add(cls._parse_version_token(to_v))
                continue
            if attr_name.startswith(prefix_downgrade):
                from_v, to_v = attr_name[len(prefix_downgrade):].split("_to_", 1)
                versions.add(cls._parse_version_token(from_v))
                versions.add(cls._parse_version_token(to_v))

        return versions

    @staticmethod
    def _parse_version_token(token: str) -> _Version:
        """Parse a version token like 'v1_2' into (1, 2)."""
        trimmed = token.removeprefix("v")
        major, minor = trimmed.split("_", 1)
        return (int(major), int(minor))

    @staticmethod
    def _version_token(version: _Version) -> str:
        return f"v{version[0]}_{version[1]}"

    @classmethod
    def _get_handler(cls, flow_type: str, start: _Version, end: _Version) -> _MigrationFn | None:
        if start < end:
            method_name = f"_{flow_type}_upgrade_{cls._version_token(start)}_to_{cls._version_token(end)}"
        else:
            method_name = f"_{flow_type}_downgrade_{cls._version_token(start)}_to_{cls._version_token(end)}"

        handler = getattr(cls, method_name, None)
        return handler

    @classmethod
    def _build_linear_path(cls, current: _Version, target: _Version, versions: set[_Version]) -> list[_Edge]:
        """Build an ordered list of version-to-version steps between current and target."""
        if current == target:
            return []

        known_versions = sorted(versions | {current, target})
        if current not in known_versions or target not in known_versions:
            raise ValueError(f"Unable to build migration path from {current} to {target}")

        current_idx = known_versions.index(current)
        target_idx = known_versions.index(target)

        edges: list[VersionMigrations._Edge] = []
        if current_idx < target_idx:
            for idx in range(current_idx, target_idx):
                edges.append((known_versions[idx], known_versions[idx + 1]))
        else:
            for idx in range(current_idx, target_idx, -1):
                edges.append((known_versions[idx], known_versions[idx - 1]))

        return edges

    @classmethod
    async def _migrate(
        cls,
        flow_type: str,
        current_major_version: int,
        current_minor_version: int,
        target_major_version: int,
        target_minor_version: int,
        flow_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Run all migration steps needed to move flow data from current to target version."""
        current = cls._version(current_major_version, current_minor_version)
        target = cls._version(target_major_version, target_minor_version)
        result = copy.deepcopy(flow_data)

        known_versions = cls._iter_known_versions(flow_type)
        steps = cls._build_linear_path(current, target, known_versions)

        for start, end in steps:
            handler = cls._get_handler(flow_type, start, end)
            if handler is None:
                direction = "upgrade" if start < end else "downgrade"
                raise NotImplementedError(
                    f"No {flow_type} {direction} migration found for {start} -> {end}. "
                    f"Expected method name pattern: "
                    f"'_{flow_type}_{direction}_{cls._version_token(start)}_to_{cls._version_token(end)}'."
                )
            result = await handler(result)

        return result

    @staticmethod
    async def migrate_config_flow(
        current_major_version: int,
        current_minor_version: int,
        target_major_version: int,
        target_minor_version: int,
        config_flow_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Migrate config flow data (devices and credentials) between entry versions."""
        return await VersionMigrations._migrate(
            flow_type="config",
            current_major_version=current_major_version,
            current_minor_version=current_minor_version,
            target_major_version=target_major_version,
            target_minor_version=target_minor_version,
            flow_data=config_flow_data,
        )

    @staticmethod
    async def migrate_options_flow(
        current_major_version: int,
        current_minor_version: int,
        target_major_version: int,
        target_minor_version: int,
        options_flow_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Migrate options flow data (entities) between entry versions."""
        return await VersionMigrations._migrate(
            flow_type="options",
            current_major_version=current_major_version,
            current_minor_version=current_minor_version,
            target_major_version=target_major_version,
            target_minor_version=target_minor_version,
            flow_data=options_flow_data,
        )

    # Migration method naming convention:
    # _config_upgrade_vX_Y_to_vA_B / _config_downgrade_vA_B_to_vX_Y
    # _options_upgrade_vX_Y_to_vA_B / _options_downgrade_vA_B_to_vX_Y

    @staticmethod
    async def _config_upgrade_v1_1_to_v2_1(config_flow_data: dict[str, Any]) -> dict[str, Any]:
        """Move auth from each device's connection info into top-level credentials."""
        data = copy.deepcopy(config_flow_data)

        devices = data.get(DICT_KEYS["DEVICES"], copy.deepcopy(DEFAULTS["DEVICES"]))
        device_items = devices.get(DICT_KEYS["DEVICE_ITEMS"], {})
        credentials = data.get(DICT_KEYS["CREDENTIALS"], copy.deepcopy(DEFAULTS["CREDENTIALS"]))

        for device_id, device in device_items.items():
            conn_info = device.get(DICT_KEYS["DEVICE_CONNECTION_INFO"], {})
            auth = conn_info.get(DICT_KEYS["DEVICE_CONNECTION_INFO_AUTH"], {})

            credential = credentials.get(device_id, {})

            credential = {
                DICT_KEYS["USER"]: auth.get(DICT_KEYS["USER"], DEFAULTS["USER"]),
                DICT_KEYS["PASS"]: auth.get(DICT_KEYS["PASS"], DEFAULTS["PASS"]),
            }

            credentials[device_id] = credential
            conn_info.pop(DICT_KEYS["DEVICE_CONNECTION_INFO_AUTH"], None)

        data[DICT_KEYS["DEVICES"]] = devices
        data[DICT_KEYS["CREDENTIALS"]] = credentials
        return data

    @staticmethod
    async def _config_downgrade_v2_1_to_v1_1(config_flow_data: dict[str, Any]) -> dict[str, Any]:
        """Move credentials back into each device's connection info auth section."""
        data = copy.deepcopy(config_flow_data)

        devices = data.get(DICT_KEYS["DEVICES"], copy.deepcopy(DEFAULTS["DEVICES"]))
        device_items = devices.get(DICT_KEYS["DEVICE_ITEMS"], {})
        credentials = data.get("credentials", {})

        for device_id, device in device_items.items():
            conn_info = device.setdefault(DICT_KEYS["DEVICE_CONNECTION_INFO"], {})
            credential = credentials.get(device_id, {})

            conn_info[DICT_KEYS["DEVICE_CONNECTION_INFO_AUTH"]] = {
                DICT_KEYS["USER"]: credential.get(DICT_KEYS["USER"], DEFAULTS["USER"]),
                DICT_KEYS["PASS"]: credential.get(DICT_KEYS["PASS"], DEFAULTS["PASS"]),
            }

        data[DICT_KEYS["DEVICES"]] = devices
        data.pop("credentials", None)
        return data

    @staticmethod
    async def _options_upgrade_v1_1_to_v2_1(options_flow_data: dict[str, Any]) -> dict[str, Any]:
        """No options schema changes for v1.1 -> v2.1."""
        return copy.deepcopy(options_flow_data)

    @staticmethod
    async def _options_downgrade_v2_1_to_v1_1(options_flow_data: dict[str, Any]) -> dict[str, Any]:
        """No options schema changes for v2.1 -> v1.1."""
        return copy.deepcopy(options_flow_data)
