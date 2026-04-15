# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\const.py                                                                     #
# Repository: tesira_ttp                                                                                               #
# Created Date: Saturday, March 28th 2026, 10:45:20 PM                                                                 #
# Last Modified: Wednesday, April 15th 2026, 10:12:08 PM                                                               #
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
PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.BINARY_SENSOR]

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
    "ENTITIES": "entities"
}

CONFIG_MODES = {
    "INIT": "init",
    "RECONFIGURE": "reconfigure"
}

DEFAULT_DEVICES = {
    "items": {},
    "primary": None
}

SCHEMA_FIELDS = {
    "instance_tag": {
        "label": "Instance Tag",
        "type": "string",
        "default": "",
        "required": True
    },
    "channel": {
        "label": "Channel",
        "type": "integer",
        "default": 1,
        "required": True
    },
    "subscribe": {
        "label": "Live Updates",
        "type": "boolean",
        "default": False,
        "required": True
    },
    "device": {
        "label": "Device",
        "type": "device_list",
        "default": None,
        "required": False
    }
}

BLOCK_SCHEMA_DATA = {
    "level": {
        "label": "Level",
        "supported_entity_types": ["media_player", "button"],
        "fields": ["device", "instance_tag", "channel", "subscribe"]
    }
}

SUPPORTED_BLOCKS = {}
DEFAULT_ENTITIES = []

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
    "ENTITIES": DEFAULT_ENTITIES
}
