# #################################################################################################################### #
# Filename: \custom_components\tesira_ttp\config_flow.py                                                               #
# Repository: tesira_ttp                                                                                               #
# Created Date: Thursday, March 19th 2026, 12:56:52 AM                                                                 #
# Last Modified: Wednesday, April 15th 2026, 11:18:43 PM                                                               #
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
import copy
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DICT_KEYS, DEFAULTS, CONFIG_MODES, SUPPORTED_BLOCKS, BLOCK_SCHEMA_DATA
from .tesira_client import TesiraClient
from .util import gen_device_id, gen_device_dict, gen_entity_dict, _redact_device, _devices, _entities, _device_name_map, _entity_name_map, TesiraTTPException
from .schemas import _device_schema, _control_schema, _hub, _entity_schema

_LOGGER = logging.getLogger(__name__)

class TesiraTtpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @property
    def _devices(self) -> dict[str, Any]:
        """Return a copy of the devices dict from the config entry data, or defaults if not available"""
        return _devices(self.context.get("entry"))

    async def _connectivity_test(self, host: str, port: int, proto: str, user: str, pwrd: str) -> tuple[dict[str, Any] | None, str | None]:
        # Validate credentials/connectivity and return device info or a flow error key.
        try:
            client = TesiraClient(host=host, port=port, proto=proto, username=user, password=pwrd)
            await client.connect()
            if client._conn is not None:
                try:
                    device_info = await client.device_info()
                    device_info = device_info["info"]
                    _LOGGER.debug("Connectivity test successful: Device Info: %s", device_info)
                    return device_info, None
                except Exception as e:
                    _LOGGER.debug("Connectivity test succeeded but failed to get device info: %s", e)
                    return None, "device_info_failed"
                finally:
                    await client.disconnect()
            else:
                raise ConnectionError("Failed to establish connection")
        except TesiraClient.InvalidCredentials as e:
            _LOGGER.debug("Connectivity test failed: %s", e)
            return None, "invalid_credentials"
        except TesiraClient.AuthenticationUnsupportedError as e:
            _LOGGER.debug("Connectivity test failed: %s", e)
            return None, "unsupported_authentication"
        except Exception as e:
            _LOGGER.exception("Connectivity test failed: %s", e)
            return None, "cannot_connect"

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Collect the hub title before requesting device connection details.
        form_errors: dict[str, str] = {}
        form_data: dict[str, Any] = {}

        if user_input is not None:
            form_data[DICT_KEYS["HUB_TITLE"]] = user_input[DICT_KEYS["HUB_TITLE"]]

            self.context[DICT_KEYS["HUB_TITLE"]] = form_data[DICT_KEYS["HUB_TITLE"]]
            return self.async_show_form(step_id="add_device", data_schema=_device_schema(), errors={})

        return self.async_show_form(step_id="user", data_schema=_hub(form_data), errors=form_errors)

    async def async_step_add_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Add a device in setup mode or reconfigure mode.
        form_errors: dict[str, str] = {}
        entry = self.context.get("entry")
        mode = CONFIG_MODES["RECONFIGURE"] if entry else CONFIG_MODES["INIT"]
        form_data: dict[str, Any] = {}

        if user_input is not None:
            # Read connection settings from the form.
            form_data[DICT_KEYS["HOST"]] = user_input[DICT_KEYS["HOST"]]
            form_data[DICT_KEYS["PORT"]] = user_input[DICT_KEYS["PORT"]]
            form_data[DICT_KEYS["PROTO"]] = user_input[DICT_KEYS["PROTO"]]
            form_data[DICT_KEYS["USER"]] = user_input[DICT_KEYS["USER"]]
            pwrd = user_input[DICT_KEYS["PASS"]]

            devices = self._devices

            device_info, error = await self._connectivity_test(form_data[DICT_KEYS["HOST"]], form_data[DICT_KEYS["PORT"]], form_data[DICT_KEYS["PROTO"]], form_data[DICT_KEYS["USER"]], pwrd)
            if error:
                return self.async_show_form(step_id="add_device", data_schema=_device_schema(form_data), errors={"base": error})

            # Build a stable device ID and persisted device payload.
            device_id = gen_device_id(deviceModel=device_info["deviceModel"], deviceRevision=device_info["deviceRevision"], serialNumber=device_info["serialNumber"])
            device = gen_device_dict(form_data[DICT_KEYS["HOST"]], form_data[DICT_KEYS["PORT"]], form_data[DICT_KEYS["PROTO"]], form_data[DICT_KEYS["USER"]], pwrd, device_info)

            # Prevent duplicate entries for the same discovered device.
            if device_id in devices["items"]:
                _LOGGER.debug("Device with ID %s already exists in config, skipping addition", device_id)
                form_errors["base"] = "device_exists"
                return self.async_show_form(step_id="add_device", data_schema=_device_schema(form_data), errors=form_errors)

            # Create a new entry during onboarding, otherwise update and reload the existing entry.
            if mode == CONFIG_MODES["INIT"]:
                title: str = self.context.get(DICT_KEYS["HUB_TITLE"])
                devices["items"][device_id] = device
                devices["primary"] = device_id
                _LOGGER.debug("Added new device: %s", _redact_device(device))
                return self.async_create_entry(title=title, data={DICT_KEYS["DEVICES"]: devices})
            else:
                entry = self.context['entry']
                devices["items"][device_id] = device
                _LOGGER.debug("Added new device: %s", _redact_device(device))
                return self.async_update_reload_and_abort(entry, data={DICT_KEYS["DEVICES"]: devices}, reason="device_added")

        return self.async_show_form(step_id="add_device", data_schema=_device_schema(), errors=form_errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Show the top-level reconfiguration menu.
        self.context['entry'] = self._get_reconfigure_entry()
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=["edit_hub_title", "devices"],
        )

    async def async_step_devices(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Show device management actions.
        return self.async_show_menu(
            step_id="devices",
            menu_options=["add_device", "select_device", "remove_device", "change_primary"],
        )

    async def async_step_select_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Let the user choose which configured device to edit.
        names = _device_name_map(self._devices)
        if not names:
            return self.async_abort(reason="no_devices")

        if user_input is None:
            schema = vol.Schema({vol.Required("select"): vol.In(list(names.keys()))})
            return self.async_show_form(step_id="select_device", data_schema=schema, errors={})

        # Store the selected device ID and open the edit form with current defaults.
        edit_id = names[user_input["select"]]
        self.context["edit_id"] = edit_id
        defaults = self._devices["items"][edit_id]["connection_info"]
        return self.async_show_form(step_id="edit_device", data_schema=_device_schema(defaults), errors={})

    async def async_step_edit_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Update connection settings for a selected device.
        form_errors: dict[str, str] = {}
        form_data: dict[str, Any] = {}
        entry = self.context.get("entry")
        edit_id = self.context.get("edit_id")
        if edit_id is None:
            # Defensive guard for invalid flow state.
            return self.async_abort(reason="unknown")
        # Pre-fill the form with existing connection settings.
        existing_device = self._devices["items"].get(edit_id)
        defaults = existing_device["connection_info"] if existing_device else {}

        if user_input is not None:
            # Read and validate updated connection settings.
            form_data[DICT_KEYS["HOST"]] = user_input[DICT_KEYS["HOST"]]
            form_data[DICT_KEYS["PORT"]] = user_input[DICT_KEYS["PORT"]]
            form_data[DICT_KEYS["PROTO"]] = user_input[DICT_KEYS["PROTO"]]
            form_data[DICT_KEYS["USER"]] = user_input[DICT_KEYS["USER"]]
            pwrd = user_input[DICT_KEYS["PASS"]]

            devices = self._devices

            # Reject changes when the updated connection cannot be validated.
            device_info, error = await self._connectivity_test(form_data[DICT_KEYS["HOST"]], form_data[DICT_KEYS["PORT"]], form_data[DICT_KEYS["PROTO"]], form_data[DICT_KEYS["USER"]], pwrd)
            if error:
                return self.async_show_form(step_id="edit_device", data_schema=_device_schema(form_data), errors={"base": error})

            # Rebuild ID and payload from the validated endpoint.
            device_id = gen_device_id(deviceModel=device_info["deviceModel"], deviceRevision=device_info["deviceRevision"], serialNumber=device_info["serialNumber"])
            device = gen_device_dict(form_data[DICT_KEYS["HOST"]], form_data[DICT_KEYS["PORT"]], form_data[DICT_KEYS["PROTO"]], form_data[DICT_KEYS["USER"]], pwrd, device_info)

            if device_id != edit_id:
                # Reject edits that point to a different physical device.
                _LOGGER.error("Device ID mismatch: expected %s but got %s. This should never happen.", edit_id, device_id)
                form_errors["base"] = "different_device"
                return self.async_show_form(step_id="edit_device", data_schema=_device_schema(form_data), errors=form_errors)

            if device_id not in devices["items"]:
                # Defensive guard if the original device is missing.
                _LOGGER.error("Device ID %s not found in existing config. This should never happen.", device_id)
                form_errors["base"] = "device_not_found"
                return self.async_show_form(step_id="edit_device", data_schema=_device_schema(form_data), errors=form_errors)

            devices["items"][device_id] = device
            _LOGGER.debug("Updated existing device: %s", _redact_device(device))
            return self.async_update_reload_and_abort(entry, data={DICT_KEYS["DEVICES"]: devices}, reason="device_updated")

        return self.async_show_form(step_id="edit_device", data_schema=_device_schema(defaults), errors=form_errors)

    async def async_step_remove_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Remove a non-primary device from the config.
        form_errors: dict[str, str] = {}
        entry = self.context.get("entry")
        names = _device_name_map(self._devices)
        if not names:
            return self.async_abort(reason="no_devices")

        # Show device choices by display name.
        schema = vol.Schema({vol.Required("select"): vol.In(list(names.keys()))})

        if user_input is None:
            return self.async_show_form(step_id="remove_device", data_schema=schema, errors={})

        # Remove the selected device and reload the entry.
        remove_id = names[user_input["select"]]
        devices = self._devices
        if devices["primary"] == remove_id:
            # Require changing primary first to keep config valid.
            _LOGGER.error("Cannot remove primary device, please change primary device first.")
            form_errors["base"] = "cannot_remove_primary"
            return self.async_show_form(step_id="remove_device", data_schema=schema, errors=form_errors)

        if remove_id not in devices["items"]:
            # Defensive guard if selection is stale.
            _LOGGER.error("Device ID %s not found in existing config. This should never happen.", remove_id)
            form_errors["base"] = "device_not_found"
            return self.async_show_form(step_id="remove_device", data_schema=schema, errors=form_errors)

        devices["items"].pop(remove_id)
        _LOGGER.debug("Removed device with ID %s", remove_id)
        return self.async_update_reload_and_abort(entry, data={DICT_KEYS["DEVICES"]: devices}, reason="device_removed")

    async def async_step_change_primary(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Change which configured device is marked as primary.
        form_errors: dict[str, str] = {}
        entry = self.context.get("entry")
        names = _device_name_map(self._devices)
        if not names:
            # Cannot select a primary device when none exist.
            return self.async_abort(reason="no_devices")

        schema = vol.Schema({vol.Required("select"): vol.In(list(names.keys()))})

        if user_input is None:
            return self.async_show_form(step_id="change_primary", data_schema=schema, errors={})

        new_primary_device = names[user_input["select"]]
        devices = self._devices
        if devices["primary"] == new_primary_device:
            # No-op guard when the selected device is already primary.
            _LOGGER.debug("Selected device is already primary, no changes made.")
            form_errors["base"] = "already_primary"
            return self.async_show_form(step_id="change_primary", data_schema=schema, errors=form_errors)
        if new_primary_device not in devices["items"]:
            # Defensive guard if selection is stale.
            _LOGGER.error("Device ID %s not found in existing config. This should never happen.", new_primary_device)
            form_errors["base"] = "device_not_found"
            return self.async_show_form(step_id="change_primary", data_schema=schema, errors=form_errors)

        devices["primary"] = new_primary_device
        _LOGGER.debug("Changed primary device to ID %s", new_primary_device)
        return self.async_update_reload_and_abort(entry, data={DICT_KEYS["DEVICES"]: devices}, reason="primary_changed")

    async def async_step_edit_hub_title(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Update the display title for this hub entry.
        form_errors: dict[str, str] = {}

        entry = self.context['entry']
        defaults = {
            DICT_KEYS["HUB_TITLE"]: entry.title
        }

        if user_input is not None:
            title = user_input[DICT_KEYS["HUB_TITLE"]]

            return self.async_update_reload_and_abort(entry, title=title)

        return self.async_show_form(step_id="edit_hub_title", data_schema=_hub(defaults), errors=form_errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return TesiraTtpOptionsFlow(config_entry)

class TesiraTtpOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # OptionsFlow defines a read-only `config_entry` property; use base init to set it.
        self._config_entry = config_entry
        self._edit_index: int | None = None

    @property
    def _entities(self) -> list[dict[str, Any]]:
        """Return a copy of the entities list from the config entry options, or defaults if not available"""
        return _entities(self.config_entry)

    @property
    def _devices(self) -> dict[str, Any]:
        """Return a copy of the devices dict from the config entry options, or defaults if not available"""
        return _devices(self.config_entry)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Show the options flow menu.
        return self.async_show_menu(
            step_id="init",
            menu_options=["select_type", "select_entity", "remove_entity"],
        )

    async def async_step_select_type(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Select a DSP block type for a new entity.
        form_errors: dict[str, str] = {}
        form_data: dict[str, Any] = {}

        if not SUPPORTED_BLOCKS:
            return self.async_abort(reason="no_supported_blocks")

        if user_input is None:
            # Show supported block types.
            schema = vol.Schema({vol.Required("select"): vol.In(list(SUPPORTED_BLOCKS.keys()))})
            return self.async_show_form(step_id="select_type", data_schema=schema, errors=form_errors)

        block_type = SUPPORTED_BLOCKS[user_input["select"]]
        self.context["block_type"] = block_type
        return self.async_show_form(step_id="add_entity", data_schema=_entity_schema(block_type=block_type, device_names=_device_name_map(self._devices)), errors={})

    async def async_step_add_entity(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Collect values and append a new entity definition.
        form_errors: dict[str, str] = {}
        block_type = self.context.get("block_type")
        device_names = _device_name_map(self._devices)
        if user_input is None:
            return self.async_show_form(step_id="add_entity", data_schema=_entity_schema(block_type=block_type, device_names=device_names), errors=form_errors)

        # Build the entity payload from schema-defined fields.
        entity = gen_entity_dict(block_type=block_type, form_data=user_input, device_names=device_names)

        entities = self._entities
        entities.append(entity)


        return self.async_create_entry(title="", data={DICT_KEYS["ENTITIES"]: entities})

    async def async_step_select_entity(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Let the user choose which configured entity to edit.
        entities = _entity_name_map(self._entities)
        if not entities:
            return self.async_abort(reason="no_entities")

        if user_input is None:
            schema = vol.Schema({vol.Required("select"): vol.In(list(entities.keys()))})
            return self.async_show_form(step_id="select_entity", data_schema=schema, errors={})

        entity_names = list(entities.keys())
        self._edit_index = entity_names.index(user_input["select"])
        block_type = self._entities[self._edit_index].get("block_type")
        self.context["block_type"] = block_type
        device_names = _device_name_map(self._devices)
        device_id_to_name = {v: k for k, v in device_names.items()}
        entity = self._entities[self._edit_index]
        defaults = {
            field: device_id_to_name.get(entity.get(field), "None") if field == "device" else entity.get(field)
            for field in BLOCK_SCHEMA_DATA.get(block_type, {}).get("fields", [])
        }
        return self.async_show_form(step_id="edit_entity", data_schema=_entity_schema(block_type=block_type, device_names=device_names, defaults=defaults), errors={})

    async def async_step_edit_entity(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Apply updated values to the selected entity.
        if self._edit_index is None:
            return self.async_abort(reason="unknown")

        block_type = self.context.get("block_type")
        device_names = _device_name_map(self._devices)
        device_id_to_name = {v: k for k, v in device_names.items()}
        entity = self._entities[self._edit_index]
        defaults = {
            field: device_id_to_name.get(entity.get(field), "None") if field == "device" else entity.get(field)
            for field in BLOCK_SCHEMA_DATA.get(block_type, {}).get("fields", [])
        }

        if user_input is None:
            return self.async_show_form(step_id="edit_entity", data_schema=_entity_schema(block_type=block_type, device_names=device_names, defaults=defaults), errors={})

        entities = self._entities
        entities[self._edit_index] = gen_entity_dict(block_type=block_type, form_data=user_input, device_names=device_names)
        self._edit_index = None
        return self.async_create_entry(title="", data={DICT_KEYS["ENTITIES"]: entities})

    async def async_step_remove_entity(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        entities = _entity_name_map(self._entities)
        if not entities:
            return self.async_abort(reason="no_entities")

        if user_input is None:
            schema = vol.Schema({vol.Required("select"): cv.multi_select(entities)})
            return self.async_show_form(step_id="remove_entity", data_schema=schema, errors={})

        selected_entities = set(user_input["select"])
        entity_names = list(entities.keys())
        selected_indices = {entity_names.index(name) for name in selected_entities if name in entity_names}
        items = [c for i, c in enumerate(self._entities) if i not in selected_indices]

        return self.async_create_entry(title="", data={DICT_KEYS["ENTITIES"]: items})
