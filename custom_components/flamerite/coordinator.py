"""Coordinator for the Flamerite Fireplace integration."""

from datetime import timedelta
import logging

from flamerite_bt.device import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_NAME, UPDATE_INTERVAL_MS

_LOGGER = logging.getLogger(__name__)

type FlameriteConfigEntry = ConfigEntry[FlameriteDataUpdateCoordinator]


class FlameriteDataUpdateCoordinator(DataUpdateCoordinator[Device]):
    """Flamerite data update coordinator."""

    config_entry: FlameriteConfigEntry
    _device: Device

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: FlameriteConfigEntry,
        device: Device,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DEFAULT_NAME,
            update_interval=timedelta(milliseconds=UPDATE_INTERVAL_MS),
        )
        self._device = device

    async def _async_update_data(self):
        """Update the device state."""
        await self._device.query_state()
        return self._device

    @property
    def device(self) -> Device:
        """Return underlying device reference."""
        return self._device
