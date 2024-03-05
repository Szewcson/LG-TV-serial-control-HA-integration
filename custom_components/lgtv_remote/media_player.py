"""Support for LG TV RS232 Media Player."""
import asyncio
from typing import Any, Optional

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.components.media_player.const import (
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

DOMAIN = "lg_tv_rs232"

async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the LG TV RS232 media player entity based on a config entry."""
    # Get the LgTV instance stored in hass.data from __init__.py
    lgtv = hass.data[DOMAIN][config_entry.entry_id]

    # Create the media player entity and add it to the platform
    async_add_entities([LGRs232MediaPlayer(lgtv)])


class LGRs232MediaPlayer(MediaPlayerEntity):
    """Representation of the LG TV RS232 media player."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, lgtv):
        """Initialize the LG TV RS232 media player."""
        self._lgtv = lgtv
        self._attr_name = f"LG TV RS232 {lgtv._id}"  # Entity name based on TV ID
        self._attr_state = MediaPlayerState.OFF
        self._attr_volume_level = None
        self._attr_is_volume_muted = None
        self._attr_source = None
        self._attr_source_list = lgtv.sources

    async def async_update(self) -> None:
        """Fetch state from the TV."""
        # Ensure the TV's status is updated
        await self.hass.async_add_executor_job(self._lgtv.update_status)
        
        # Update entity attributes based on the TV's current state
        self._attr_state = (
            MediaPlayerState.ON if self._lgtv.is_on else MediaPlayerState.OFF
        )
        if self._attr_state == MediaPlayerState.ON:
            self._attr_volume_level = self._lgtv.volume / 100
            self._attr_is_volume_muted = self._lgtv.muted
            self._attr_source = self._lgtv.input

    async def async_turn_on(self) -> None:
        """Turn the TV on."""
        await self.hass.async_add_executor_job(self._lgtv.request, "power", "on")
        self._attr_state = MediaPlayerState.ON

    async def async_turn_off(self) -> None:
        """Turn the TV off."""
        await self.hass.async_add_executor_job(self._lgtv.request, "power", "off")
        self._attr_state = MediaPlayerState.OFF

    async def async_set_volume_level(self, volume: float) -> None:
        """Set the volume level."""
        volume_percent = int(volume * 100)
        await self.hass.async_add_executor_job(self._lgtv.request, "volume", str(volume_percent))
        self._attr_volume_level = volume

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the volume."""
        mute_state = "on" if mute else "off"
        await self.hass.async_add_executor_job(self._lgtv.request, "sound", mute_state)
        self._attr_is_volume_muted = mute

    async def async_select_source(self, source: str) -> None:
        """Set the input source."""
        if source in self._lgtv.sources:
            await self.hass.async_add_executor_job(self._lgtv.request, "input", source)
            self._attr_source = source

