"""Support for LG TV RS232 Remote."""
import asyncio
from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    RemoteEntity,
)
from .const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import voluptuous as vol

async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the LG TV RS232 remote entity based on a config entry."""
    # Get the LgTV instance stored in hass.data from __init__.py
    lgtv = hass.data[DOMAIN][config_entry.entry_id]

    # Create the remote entity and add it to the platform
    async_add_entities([LGRs232Remote(lgtv)])

class LGRs232Remote(RemoteEntity):
    """Representation of the LG TV RS232 remote."""

    def __init__(self, lgtv):
        """Initialize the LG TV RS232 remote."""
        self._lgtv = lgtv
        self._attr_is_on = lgtv.is_on
        self._attr_name = f"LG TV RS232 {lgtv._id}"  # Entity name based on TV ID

    @property
    def is_on(self) -> bool:
        """Return True if the TV is on."""
        return self._lgtv.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the TV."""
        await self.hass.async_add_executor_job(self._lgtv.request, "power", "on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the TV."""
        await self.hass.async_add_executor_job(self._lgtv.request, "power", "off")

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to the TV."""
        # Extracting optional parameters for command sending
        num_repeats = kwargs[ATTR_NUM_REPEATS]
        delay = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)

        for _ in range(num_repeats):
            for single_command in command:
                raw_cmd, raw_arg = single_command.split("_")
                await self.hass.async_add_executor_job(self._lgtv.request, raw_cmd, raw_arg)

                await asyncio.sleep(delay)  # Delay between command sends
