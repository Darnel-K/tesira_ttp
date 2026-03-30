# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\util.py                                                                      #
# Repository: tesira_ttp                                                                                               #
# Created Date: Sunday, March 22nd 2026, 10:04:37 PM                                                                   #
# Last Modified: Thursday, March 26th 2026, 12:25:23 AM                                                                #
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

from typing import Any, Dict

import voluptuous as vol

# =====================================================================
# Schema Helpers
# =====================================================================
def schema_with_defaults(
    base_schema: vol.Schema, defaults: Dict[str, Any]
) -> vol.Schema:
    """
    Create a new voluptuous Schema with runtime default values injected.

    This **does not** modify the passed-in base schema.

    Args:
        base_schema: The original schema to copy fields from.
        defaults: A dictionary mapping field names -> default values.

    Returns:
        A new vol.Schema instance where matching fields are replaced with
        new Required/Optional fields containing default values.
    """
    new_fields: Dict[Any, Any] = {}

    # base_schema.schema contains {vol.Required/vol.Optional: validator}
    for key, validator in base_schema.schema.items():
        field_name = key.schema  # the raw field name string

        if field_name in defaults:
            default_value = defaults[field_name]

            # Replace field with one that has a default applied
            if isinstance(key, vol.Required):
                new_fields[vol.Required(field_name, default=default_value)] = validator
            else:
                new_fields[vol.Optional(field_name, default=default_value)] = validator
        else:
            # Leave untouched
            new_fields[key] = validator

    return vol.Schema(new_fields)
