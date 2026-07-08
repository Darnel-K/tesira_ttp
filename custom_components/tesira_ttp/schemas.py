# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\schemas.py                                                                   #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Wednesday, July 8th 2026, 1:27:02 AM                                                                  #
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

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from typing import Any
from homeassistant.helpers.selector import selector
from .const import DOMAIN, DICT_KEYS, DEFAULTS, BLOCK_SCHEMA_DATA, SCHEMA_FIELDS

_LOGGER = logging.getLogger(__name__)

def _hub(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(DICT_KEYS["HUB_TITLE"], default=d.get(DICT_KEYS["HUB_TITLE"], "")): cv.string
        }
    )

def _device_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(DICT_KEYS["HOST"], default=d.get(DICT_KEYS["HOST"], DEFAULTS["HOST"])): cv.string,
            vol.Optional(DICT_KEYS["PORT"], default=d.get(DICT_KEYS["PORT"], DEFAULTS["PORT"])): cv.port,
            vol.Required(DICT_KEYS["PROTO"], default=d.get(DICT_KEYS["PROTO"], DEFAULTS["PROTO"])): selector({
                "select": {
                    "options": [
                        {"value": "ssh", "label": "SSH"},
                        {"value": "telnet", "label": "Telnet"}
                    ]
                }
            }),
            vol.Optional(DICT_KEYS["USER"], default=d.get(DICT_KEYS["USER"], DEFAULTS["USER"])): cv.string,
            vol.Optional(DICT_KEYS["PASS"], default=d.get(DICT_KEYS["PASS"], DEFAULTS["PASS"])): cv.string
        }
    )

def _entity_schema(defaults: dict[str, Any] | None = None, block_type: str | None = None, device_names: dict[str, str] | None = None) -> vol.Schema:
    d = defaults or {}
    if block_type not in BLOCK_SCHEMA_DATA:
        raise ValueError(f"Unsupported block type: {block_type}")

    block_data = BLOCK_SCHEMA_DATA[block_type]
    fields = block_data.get(DICT_KEYS["ENTITY_BLOCK_FIELDS"], [])
    field_options = block_data.get(DICT_KEYS["ENTITY_BLOCK_FIELD_OPTIONS"], None)
    schema_dict = {}

    # Convert declarative field metadata into voluptuous validators at runtime.
    for field in fields:
        field_info = SCHEMA_FIELDS.get(field)
        default_value = d.get(field, field_info.get("default", None))
        required = field_info.get("required", False)
        field_type = field_info.get("type", "string")
        options = None

        if field_options and field in field_options:
            options = field_options.get(field, None)
            if options.get(DICT_KEYS["ENTITY_FIELD_TYPE_OVERRIDE"], None) is not None:
                field_type = options[DICT_KEYS["ENTITY_FIELD_TYPE_OVERRIDE"]]

        if field_type == "string":
            validator = cv.string
        elif field_type == "integer":
            if isinstance(options, dict):
                if ("min" in options and isinstance(options["min"], int)) and ("max" in options and isinstance(options["max"], int)):
                    validator = vol.All(vol.Coerce(int), vol.Range(min=options["min"], max=options["max"]))
                else:
                    raise ValueError(f"Invalid options for integer field '{field}', cannot mix int and float: {options}")
            else:
                validator = vol.Coerce(int)
        elif field_type == "float":
            if isinstance(options, dict):
                if ("min" in options and isinstance(options["min"], (int, float))) and ("max" in options and isinstance(options["max"], (int, float))):
                    validator = vol.All(vol.Coerce(float), vol.Range(min=options["min"], max=options["max"]))
                else:
                    raise ValueError(f"Invalid options for float field '{field}': {options}")
            else:
                validator = vol.Coerce(float)
        elif field_type == "boolean":
            validator = vol.Coerce(bool)
        elif field_type == "port":
            validator = cv.port
        elif field_type == "device_list":
            if device_names is None:
                raise ValueError("device_names must be provided for device_list fields")
            keys = list(device_names.keys())
            keys.insert(0, "None")  # Allow for no device selection
            validator = vol.In(list(keys))
        else:
            raise ValueError(f"Unsupported field type: {field_type}")

        if required:
            schema_dict[vol.Required(field, default=default_value)] = validator
        else:
            schema_dict[vol.Optional(field, default=default_value)] = validator

    return vol.Schema(schema_dict)
