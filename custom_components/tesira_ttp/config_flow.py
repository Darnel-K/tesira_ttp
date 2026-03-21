# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\config_flow.py                                                               #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Saturday, March 21st 2026, 12:52:46 AM                                                                #
# Original Author: Darnel Kumar                                                                                        #
# Author Github: https://github.com/Darnel-K                                                                           #
#                                                                                                                      #
# This code complies with: https://gist.github.com/Darnel-K/8badda0cabdabb15359350f7af911c90                           #
# Copyright (c) 2026 Darnel Kumar                                                                                      #
# #################################################################################################################### #
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_CONTROLS,
    CONF_CONTROL_NAME,
    CONF_INSTANCE_TAG,
    CONF_CHANNEL,
    CONF_MIN_DB,
    CONF_MAX_DB,
    CONF_STEP_DB,
    DEFAULT_PORT,
    DEFAULT_CONTROL_NAME,
    DEFAULT_CHANNEL,
    DEFAULT_MIN_DB,
    DEFAULT_MAX_DB,
    DEFAULT_STEP_DB
)
from .tesira_client import TesiraTtpClient
from .util import schema_with_defaults

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
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
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            # Use host:port as unique key so a Tesira device is only configured once.
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            # Quick connectivity probe.
            try:
                client = TesiraTtpClient(host, port)
                await client.connect()
                await client.close()
            except Exception as e:
                _LOGGER.debug("Connectivity test failed: %s", e)
                errors["base"] = "cannot_connect"
                return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

            self.context["host"] = host
            self.context["port"] = port
            title = f"Tesira {host}:{port}"
            return self.async_create_entry(title=title, data={CONF_HOST: host, CONF_PORT: port})

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        entry = self._get_reconfigure_entry()
        defaults = {
            CONF_HOST: entry.data.get(CONF_HOST),
            CONF_PORT: entry.data.get(CONF_PORT),
        }
        schema = schema_with_defaults(STEP_USER_SCHEMA, defaults)

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            try:
                client = TesiraTtpClient(host, port)
                await client.connect()
                await client.close()
            except Exception as e:
                _LOGGER.debug("Connectivity test failed: %s", e)
                errors["base"] = "cannot_connect"
                return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

            self.context["host"] = host
            self.context["port"] = port
            return self.async_update_reload_and_abort(self._get_reconfigure_entry(), data_updates=user_input)

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
