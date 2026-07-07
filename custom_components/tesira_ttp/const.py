# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\const.py                                                                     #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Wednesday, July 8th 2026, 12:03:18 AM                                                                 #
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

from homeassistant.const import Platform

DOMAIN = "tesira_ttp"
PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.BUTTON]

DICT_KEYS = {
    "DATA_HUBS": "hubs",
    "DATA_ENTRY_HUBKEY": "entry_hubkey",
    "HUB_TITLE": "hub_title",
    "HOST": "host",
    "PORT": "port",
    "PROTO": "protocol",
    "USER": "username",
    "PASS": "password",
    "DEVICE_INFO": "device_info",
    "DEVICES": "devices",
    "CREDENTIALS": "credentials",
    "DEVICE_ITEMS": "items",
    "DEVICE_ID": "device_id",
    "DEVICE_CONNECTION_INFO": "connection_info",
    "DEVICE_CONNECTION_INFO_AUTH": "auth",
    "PRIMARY_DEVICE": "primary",
    "ENTITIES": "entities",
    "ENTITY_DEVICE_IDENTIFIERS": "identifiers",
    "CONFIG_ENTRY": "entry",
    "EDIT_ID": "edit_id",
    "ENTITY_BLOCK_TYPE": "block_type",
    "ENTITY_BLOCK_FIELDS": "fields",
    "ENTITY_BLOCK_FIELD_OPTIONS": "field_options",
    "ENTITY_BLOCK_SUPPORTED_TYPES": "supported_entity_types",
    "ENTITY_BLOCK_INSTANCE_TAG": "instance_tag",
    "ENTITY_BLOCK_CHANNEL": "channel",
    "ENTITY_BLOCK_SUBSCRIBE": "subscribe",
    "ENTITY_MIN_VALUE": "min_value",
    "ENTITY_MAX_VALUE": "max_value",
    "ENTITY_FIELD_TYPE_OVERRIDE": "field_type_override"
}

STEP_IDS = {}
ERROR_MSG = {}
ABORT_MSG = {}

CONFIG_MODES = {
    "INIT": "init",
    "RECONFIGURE": "reconfigure"
}

DEFAULT_DEVICES = {
    DICT_KEYS["DEVICE_ITEMS"]: {},
    DICT_KEYS["PRIMARY_DEVICE"]: None
}

SCHEMA_FIELDS = {
    DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"]: {
        "label": "Instance Tag",
        "type": "string",
        "default": "",
        "required": True
    },
    DICT_KEYS["ENTITY_BLOCK_CHANNEL"]: {
        "label": "Channel",
        "type": "integer",
        "default": 1,
        "required": True
    },
    DICT_KEYS["ENTITY_BLOCK_SUBSCRIBE"]: {
        "label": "Live Updates",
        "type": "boolean",
        "default": False,
        "required": True
    },
    DICT_KEYS["ENTITY_MIN_VALUE"]: {
        "label": "Minimum Value",
        "type": "float",
        "default": 0.0,
        "required": True
    },
    DICT_KEYS["ENTITY_MAX_VALUE"]: {
        "label": "Maximum Value",
        "type": "float",
        "default": 0.0,
        "required": True
    },
    DICT_KEYS["DEVICE_ID"]: {
        "label": "Device",
        "type": "device_list",
        "default": None,
        "required": False
    }
}

BLOCK_SCHEMA_DATA = {
    "level": {
        "label": "Level",
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["media_player"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"], DICT_KEYS["ENTITY_BLOCK_SUBSCRIBE"]]
    },
    "logic_state": {
        "label": "Logic State",
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["switch"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"], DICT_KEYS["ENTITY_BLOCK_SUBSCRIBE"]]
    },
    "flip_flop": {
        "label": "Flip Flop",
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["switch"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"], DICT_KEYS["ENTITY_BLOCK_SUBSCRIBE"]]
    },
    "logic_delay": {
        "label": "Logic Delay",
        DICT_KEYS["ENTITY_BLOCK_FIELD_OPTIONS"]: {
            DICT_KEYS["ENTITY_MIN_VALUE"]: {"min": 0, "max": 60000, DICT_KEYS["ENTITY_FIELD_TYPE_OVERRIDE"]: "integer"},
            DICT_KEYS["ENTITY_MAX_VALUE"]: {"min": 0, "max": 60000, DICT_KEYS["ENTITY_FIELD_TYPE_OVERRIDE"]: "integer"}
        },
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["switch", "number"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"], DICT_KEYS["ENTITY_MIN_VALUE"], DICT_KEYS["ENTITY_MAX_VALUE"]]
    },
    "logic_input": {
        "label": "Logic Input",
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["switch"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"]]
    },
    "logic_meter": {
        "label": "Logic Meter",
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["binary_sensor"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"], DICT_KEYS["ENTITY_BLOCK_SUBSCRIBE"]]
    },
    "logic_output": {
        "label": "Logic Output",
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["switch"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"]]
    },
    "logic_selector": {
        "label": "Logic Selector",
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["switch"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"], DICT_KEYS["ENTITY_BLOCK_SUBSCRIBE"]]
    },
    "logic_pulse": {
        "label": "Logic Pulse",
        DICT_KEYS["ENTITY_BLOCK_FIELD_OPTIONS"]: {
            DICT_KEYS["ENTITY_MIN_VALUE"]: {"min": 1, "max": 60000, DICT_KEYS["ENTITY_FIELD_TYPE_OVERRIDE"]: "integer"},
            DICT_KEYS["ENTITY_MAX_VALUE"]: {"min": 1, "max": 60000, DICT_KEYS["ENTITY_FIELD_TYPE_OVERRIDE"]: "integer"}
        },
        DICT_KEYS["ENTITY_BLOCK_SUPPORTED_TYPES"]: ["binary_sensor", "switch", "number", "button"],
        DICT_KEYS["ENTITY_BLOCK_FIELDS"]: [DICT_KEYS["DEVICE_ID"], DICT_KEYS["ENTITY_BLOCK_INSTANCE_TAG"], DICT_KEYS["ENTITY_BLOCK_CHANNEL"], DICT_KEYS["ENTITY_MIN_VALUE"], DICT_KEYS["ENTITY_MAX_VALUE"]]
    }
}

SUPPORTED_BLOCKS = {}
DEFAULT_ENTITIES = []
DEFAULT_CREDENTIALS = {}

# Build selector labels and default entity containers from a single block schema source.
for block_type, data in BLOCK_SCHEMA_DATA.items():
    SUPPORTED_BLOCKS[data["label"]] = block_type

# DEFAULT_ENTITIES = {
#     "preset": [],
#     "aec_input": [],
#     "aec_processing": [],
#     "aec_reference": [],
#     "anc": [],
#     "anc_input": [],
#     "av_input": [],
#     "av_output": [],
#     "avb.1_input": [],
#     "avb.1_output": [],
#     "attero_tech_input": [],
#     "attero_tech_output": [],
#     "bluetooth_control_status": [],
#     "bluetooth_input": [],
#     "bluetooth_output": [],
#     "cobranet_input": [],
#     "cobranet_output": [],
#     "dtmf_decode": [],
#     "dante_input": [],
#     "dante_mic": [],
#     "dante_output": [],
#     "ex-ubt_usb_input": [],
#     "ex-ubt_usb_output": [],
#     "input": [],
#     "lab.gruppen_amplifier": [],
#     "output": [],
#     "parle_amplifier": [],
#     "parle_microphone": [],
#     "parle_microphone_beam_outs": [],
#     "poe_amp": [],
#     "ti_control_status": [],
#     "ti_receive": [],
#     "ti_transmit": [],
#     "tesira_amplifier": [],
#     "tesiraxel_1200": [],
#     "usb_input": [],
#     "usb_output": [],
#     "voip_control_status": [],
#     "voip_receive": [],
#     "voip_transmit": [],
#     "voltera_amplifier": [],
#     "paging_control": [],
#     "paging_zone": [],
#     "auto_mixer_combiner": [],
#     "gain_sharing_auto_mixer": [],
#     "gating_auto_mixer": [],
#     "matrix_mixer": [],
#     "room_combiner": [],
#     "standard_mixer": [],
#     "feedback_suppressor": [],
#     "graphic_equalizer": [],
#     "parametric_equalizer": [],
#     "all_pass_filter": [],
#     "fir_filter": [],
#     "pass_filter": [],
#     "shelf_filter": [],
#     "uber_filter": [],
#     "crossover": [],
#     "agc": [],
#     "ai_noise_reduction": [],
#     "compressor": [],
#     "ducker": [],
#     "leveler": [],
#     "noise_gate": [],
#     "peak_limiter": [],
#     "av_router": [],
#     "router": [],
#     "source_selector": [],
#     "delay": [],
#     "command_string": [],
#     "dialer": [],
#     "hd-1": [],
#     "invert": [],
#     "level": [],
#     "mute": [],
#     "parle_processing": [],
#     "preset_button": [],
#     "voltage_control": [],
#     "audio_meter": [],
#     "signal_present_meter": [],
#     "noise_generator": [],
#     "tone_generator": [],
#     "flip_flop": [],
#     "logic_delay": [],
#     "logic_input": [],
#     "logic_meter": [],
#     "logic_output": [],
#     "logic_pulse": [],
#     "logic_selector": [],
#     "logic_sequence": [],
#     "logic_state": [],
#     "device": []
# }

DEFAULTS = {
    "HOST": "0.0.0.0",
    "PORT": 22,
    "PROTO": "ssh",
    "USER": "default",
    "PASS": "",
    "DEVICES": DEFAULT_DEVICES,
    "ENTITIES": DEFAULT_ENTITIES,
    "CREDENTIALS": DEFAULT_CREDENTIALS
}
