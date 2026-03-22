# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\util.py                                                                      #
# Repository: tesira_ttp                                                                                               #
# Created Date: Sunday, March 22nd 2026, 1:21:35 AM                                                                    #
# Last Modified: Sunday, March 22nd 2026, 5:43:18 PM                                                                   #
# Original Author: Darnel Kumar                                                                                        #
# Author Github: https://github.com/Darnel-K                                                                           #
#                                                                                                                      #
# This code complies with: https://gist.github.com/Darnel-K/8badda0cabdabb15359350f7af911c90                           #
# Copyright (c) 2026 Darnel Kumar                                                                                      #
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
