# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\migrations.py                                                                #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Sunday, May 3rd 2026, 1:16:50 AM                                                                      #
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
"""Container for config entry migration functions to handle updates to config structure across versions."""

from __future__ import annotations

from typing import Any, Awaitable, Callable
from .const import DICT_KEYS, DEFAULTS

import copy

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
