"""Config flow for LG TV RS232 integration."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, List, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,   # Add the DOMAIN constant in your const.py (e.g., "lg_tv_rs232")
    CONF_PORT,
    CONF_TV_ID,
)
from lgtv_rs232 import LgTV  # This should import your LgTV class from the library or local module.

_LOGGER = logging.getLogger(__name__)

# Function to detect available serial ports
def detect_serial_ports() -> List[str]:
    """Detect available serial ports (tty devices)."""
    ports = []
    # List available serial devices in /dev
    for filename in os.listdir("/dev"):
        if filename.startswith("tty") and filename != "tty" and os.access(f"/dev/{filename}", os.R_OK):
            ports.append(f"/dev/{filename}")
    return ports

async def wake_tv(tv, iterations, delay):
    for _ in range(iterations): # Set to num. of desired tries
        response = tv.request("power", "on")
        await asyncio.sleep(delay) # Set to num. of seconds to wait before checking power status and trying again
        if response is not False:
            break
    return response

# Define the user step schema
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT): vol.In(detect_serial_ports()),  # List detected serial ports
        vol.Optional(CONF_TV_ID, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=99)),  # Default TV ID to 0
    }
)

class LGTVRS232ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the LG TV RS232 integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Handle the initial step to set up the integration."""
        errors = {}
        if user_input is not None:
            port = user_input[CONF_PORT]
            tv_id = user_input[CONF_TV_ID]

            # Try to connect to the TV using the provided serial port and TV ID
            try:
                # Example: Attempt to connect to the TV and validate.
                tv = LgTV(port, tv_id)
                response = tv.request('power', 'check')
                if response is False:
                    response = await wake_tv(tv, 2, 1)
                    if response is not False:
                        await asyncio.sleep(10)
                        tv.request('power', 'off')
                    else:
                        raise ConnectionError('TV is not responding')

                await self.async_set_unique_id(f"lg_tv_{tv_id}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"LG TV {tv_id}", data=user_input)
            
            except ConnectionError as err:
                _LOGGER.error("Connection failed to LG TV at port %s: %s", port, err)
                del tv
                errors["base"] = "cannot_connect"
            except ValueError as err:
                _LOGGER.error("Invalid configuration for LG TV RS232: %s", err)
                del tv
                errors["base"] = "value_error"
            except Exception as err:
                _LOGGER.exception("Failed to connect to the LG TV: %s", err)
                del tv
                errors["base"] = "exception"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> LGTVRS232OptionsFlow:
        """Get the options flow for this handler."""
        return LGTVRS232OptionsFlow(config_entry)


class LGTVRS232OptionsFlow(config_entries.OptionsFlow):
    """Options flow for LG TV RS232 integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Manage the options for the custom component."""
        return await self.async_step_user()

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        """Handle the options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Options schema: User can modify the TV ID
        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TV_ID, default=self.config_entry.options.get(CONF_TV_ID, 0)
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=99)),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=options_schema
        )
