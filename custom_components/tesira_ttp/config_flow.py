# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\config_flow.py                                                               #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Friday, April 3rd 2026, 9:55:19 PM                                                                    #
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
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_IP,
    CONF_PORT,
    CONF_PROTO,
    CONF_USER,
    CONF_PASS,
    CONF_DEVICE_INFO,
    CONF_CONTROLS,
    CONF_CONTROL_NAME,
    CONF_INSTANCE_TAG,
    CONF_CHANNEL,
    CONF_MIN_DB,
    CONF_MAX_DB,
    CONF_STEP_DB,
    DEFAULT_PORT,
    DEFAULT_PROTO,
    DEFAULT_USER,
    DEFAULT_PASS,
    DEFAULT_CONTROL_NAME,
    DEFAULT_CHANNEL,
    DEFAULT_MIN_DB,
    DEFAULT_MAX_DB,
    DEFAULT_STEP_DB
)
from .tesira_client import TesiraClient
from .util import schema_with_defaults, gen_hub_key, TesiraTTPException

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(CONF_PROTO, default=DEFAULT_PROTO): selector({
            "select": {
                "options": [
                    {"value": "ssh", "label": "SSH"},
                    {"value": "telnet", "label": "Telnet"}
                ]
            }
        }),
        vol.Optional(CONF_USER, default=DEFAULT_USER): cv.string,
        vol.Optional(CONF_PASS, default=DEFAULT_PASS): cv.string
    }
)

def _control_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Optional(CONF_CONTROL_NAME, default=d.get(CONF_CONTROL_NAME, DEFAULT_CONTROL_NAME)): cv.string,
            vol.Required(CONF_INSTANCE_TAG, default=d.get(CONF_INSTANCE_TAG, "volume")): cv.string,
            vol.Optional(CONF_CHANNEL, default=int(d.get(CONF_CHANNEL, DEFAULT_CHANNEL))): vol.Coerce(int),
            vol.Optional(CONF_MIN_DB, default=float(d.get(CONF_MIN_DB, DEFAULT_MIN_DB))): vol.Coerce(float),
            vol.Optional(CONF_MAX_DB, default=float(d.get(CONF_MAX_DB, DEFAULT_MAX_DB))): vol.Coerce(float),
            vol.Optional(CONF_STEP_DB, default=float(d.get(CONF_STEP_DB, DEFAULT_STEP_DB))): vol.Coerce(float),
        }
    )

class TesiraTtpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_IP]
            port = user_input[CONF_PORT]
            proto = user_input[CONF_PROTO]
            user = user_input[CONF_USER]
            pwrd = user_input[CONF_PASS]

            # Quick connectivity probe.
            try:
                client = TesiraClient(host=host, port=port, proto=proto, username=user, password=pwrd)
                await client.connect()
                if client._conn is not None:
                    try:
                        device_info = await client.device_info()
                        await client.disconnect()
                        device_info = device_info["info"]
                        _LOGGER.debug("Connectivity test successful: Device Info: %s", device_info)
                        hub_key = gen_hub_key(deviceModel=device_info["deviceModel"], deviceRevision=device_info["deviceRevision"], serialNumber=device_info["serialNumber"])
                        # Use device_info as unique key so a Tesira device is only configured once.
                        await self.async_set_unique_id(hub_key)
                        self._abort_if_unique_id_configured()
                    except Exception as e:
                        _LOGGER.debug("Connectivity test succeeded but failed to get device info: %s", e)
                        errors["base"] = "device_info_failed"
                        await client.disconnect()
                        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)
                else:
                    raise ConnectionError("Failed to establish connection")
            except TesiraClient.InvalidCredentials as e:
                _LOGGER.debug("Connectivity test failed: %s", e)
                errors["base"] = "invalid_credentials"
                return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)
            except TesiraClient.AuthenticationUnsupportedError as e:
                _LOGGER.debug("Connectivity test failed: %s", e)
                errors["base"] = "unsupported_authentication"
                return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)
            except Exception as e:
                _LOGGER.debug("Connectivity test failed: %s", e)
                errors["base"] = "cannot_connect"
                return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

            title = f"Biamp - {device_info['deviceModel']} - {device_info['serialNumber']} - {host}:{port}"
            return self.async_create_entry(title=title, data={CONF_IP: host, CONF_PORT: port, CONF_PROTO: proto, CONF_USER: user, CONF_PASS: pwrd, CONF_DEVICE_INFO: device_info})

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        entry = self._get_reconfigure_entry()
        defaults = {
            CONF_IP: entry.data.get(CONF_IP),
            CONF_PORT: entry.data.get(CONF_PORT),
            CONF_PROTO: entry.data.get(CONF_PROTO),
            CONF_USER: entry.data.get(CONF_USER)
        }
        schema = schema_with_defaults(STEP_USER_SCHEMA, defaults)
        existing_device_info = entry.data.get(CONF_DEVICE_INFO)

        if user_input is not None:
            host = user_input[CONF_IP]
            port = user_input[CONF_PORT]
            proto = user_input[CONF_PROTO]
            user = user_input[CONF_USER]
            pwrd = user_input[CONF_PASS]

            try:
                client = TesiraClient(host=host, port=port, proto=proto, username=user, password=pwrd)
                await client.connect()
                if client._conn is not None:
                    try:
                        device_info = await client.device_info()
                        await client.disconnect()
                        device_info = device_info["info"]
                        _LOGGER.debug("Connectivity test successful: Device Info: %s", device_info)
                        if existing_device_info:
                            if device_info["serialNumber"] != existing_device_info.get("serialNumber") or device_info["deviceModel"] != existing_device_info.get("deviceModel") or device_info["deviceRevision"] != existing_device_info.get("deviceRevision"):
                                _LOGGER.warning("Device info has changed from %s to %s. This may indicate that the connection parameters now point to a different Tesira device.", existing_device_info, device_info)
                                raise TesiraTTPException.NotPermitted("Device info has changed. This may indicate that the connection parameters now point to a different Tesira device.")
                    except TesiraTTPException.NotPermitted as e:
                        _LOGGER.debug("Connectivity test succeeded but device info has changed: %s", e)
                        errors["base"] = "different_device"
                        await client.disconnect()
                        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)
                    except Exception as e:
                        _LOGGER.debug("Connectivity test succeeded but failed to get device info: %s", e)
                        errors["base"] = "device_info_failed"
                        await client.disconnect()
                        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)
                else:
                    raise ConnectionError("Failed to establish connection")
            except TesiraClient.InvalidCredentials as e:
                _LOGGER.debug("Connectivity test failed: %s", e)
                errors["base"] = "invalid_credentials"
                return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)
            except TesiraClient.AuthenticationUnsupportedError as e:
                _LOGGER.debug("Connectivity test failed: %s", e)
                errors["base"] = "unsupported_authentication"
                return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)
            except Exception as e:
                _LOGGER.debug("Connectivity test failed: %s", e)
                errors["base"] = "cannot_connect"
                return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

            return self.async_update_reload_and_abort(entry, data_updates=user_input)

        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return TesiraTtpOptionsFlow(config_entry)

class TesiraTtpOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # OptionsFlow defines a read-only `config_entry` property; use base init to set it.
        self._config_entry = config_entry
        self._edit_index: int | None = None

    @property
    def _controls(self) -> list[dict[str, Any]]:
        return list(self.config_entry.options.get(CONF_CONTROLS, []))

    def _label_map(self) -> dict[str, int]:
        labels: dict[str, int] = {}
        for i, c in enumerate(self._controls):
            name = c.get(CONF_CONTROL_NAME, DEFAULT_CONTROL_NAME)
            tag = c.get(CONF_INSTANCE_TAG, "?")
            ch = c.get(CONF_CHANNEL, "?")
            label = f"{name} ({tag} ch{ch})"
            if label in labels:
                label = f"{label} [{i}]"
            labels[label] = i
        return labels

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["add", "edit", "remove"],
        )

    async def async_step_add(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="add", data_schema=_control_schema(), errors={})

        controls = self._controls
        controls.append(
            {
                CONF_CONTROL_NAME: user_input[CONF_CONTROL_NAME],
                CONF_INSTANCE_TAG: user_input[CONF_INSTANCE_TAG],
                CONF_CHANNEL: user_input[CONF_CHANNEL],
                CONF_MIN_DB: user_input[CONF_MIN_DB],
                CONF_MAX_DB: user_input[CONF_MAX_DB],
                CONF_STEP_DB: user_input[CONF_STEP_DB],
            }
        )
        return self.async_create_entry(title="", data={CONF_CONTROLS: controls})

    async def async_step_edit(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        labels = self._label_map()
        if not labels:
            return self.async_abort(reason="no_controls")

        if user_input is None:
            schema = vol.Schema({vol.Required("which"): vol.In(list(labels.keys()))})
            return self.async_show_form(step_id="edit", data_schema=schema, errors={})

        self._edit_index = labels[user_input["which"]]
        defaults = self._controls[self._edit_index]
        return self.async_show_form(step_id="edit_control", data_schema=_control_schema(defaults), errors={})

    async def async_step_edit_control(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if self._edit_index is None:
            return self.async_abort(reason="unknown")

        if user_input is None:
            defaults = self._controls[self._edit_index]
            return self.async_show_form(step_id="edit_control", data_schema=_control_schema(defaults), errors={})

        controls = self._controls
        controls[self._edit_index] = {
            CONF_CONTROL_NAME: user_input[CONF_CONTROL_NAME],
            CONF_INSTANCE_TAG: user_input[CONF_INSTANCE_TAG],
            CONF_CHANNEL: user_input[CONF_CHANNEL],
            CONF_MIN_DB: user_input[CONF_MIN_DB],
            CONF_MAX_DB: user_input[CONF_MAX_DB],
            CONF_STEP_DB: user_input[CONF_STEP_DB],
        }
        self._edit_index = None
        return self.async_create_entry(title="", data={CONF_CONTROLS: controls})

    async def async_step_remove(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        labels = self._label_map()
        if not labels:
            return self.async_abort(reason="no_controls")

        if user_input is None:
            schema = vol.Schema({vol.Required("remove"): cv.multi_select(labels)})
            return self.async_show_form(step_id="remove", data_schema=schema, errors={})

        selected_labels = set(user_input["remove"])
        selected_indices = {labels[label] for label in selected_labels}
        controls = [c for i, c in enumerate(self._controls) if i not in selected_indices]

        return self.async_create_entry(title="", data={CONF_CONTROLS: controls})
