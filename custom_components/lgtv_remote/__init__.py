"""The LG TV RS232 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_PORT, CONF_TV_ID
from lgtv_rs232 import LgTV

_LOGGER = logging.getLogger(__name__)

# This will hold the unique domain registry of the connected devices
PLATFORMS = ["remote"]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Do not support YAML setup."""
    return True

async def wake_tv(tv, iterations, delay):
    for _ in range(iterations): # Set to num. of desired tries
        response = tv.request("power", "on")
        await asyncio.sleep(delay) # Set to num. of seconds to wait before checking power status and trying again
        if response is not False:
            break
    return response

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up LG TV RS232 from a config entry."""
    port = config_entry.data[CONF_PORT]
    tv_id = config_entry.data.get(CONF_TV_ID, 0)

    try:
        lgtv = LgTV(port, tv_id)

        # Validate connection
        response = lgtv.request('power', 'check')
        if response is False:
            response = await wake_tv(tv, 2, 1)
            if response is not False:
                await asyncio.sleep(10)
                tv.request('power', 'off')
            else:
                _LOGGER.warning("Unable to communicate with LG TV at port: %s", port)
                del lgtv
                return False

        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = lgtv

    except ConnectionError as err:
        _LOGGER.error("Connection failed to LG TV at port %s: %s", port, err)
        del lgtv
        return False
    except ValueError as err:
        _LOGGER.error("Invalid configuration for LG TV RS232: %s", err)
        del lgtv
        return False
    except Exception as err:
        _LOGGER.exception("Unexpected error during LG TV setup: %s", err)
        del lgtv
        return False

    # Forward setup to platform(s)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    lgtv = hass.data[DOMAIN].pop(config_entry.entry_id, None)
    if lgtv:
        del lgtv

    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok and not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return unload_ok
