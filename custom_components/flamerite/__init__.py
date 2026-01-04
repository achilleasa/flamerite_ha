"""The Flamerite Fireplace integration."""

from __future__ import annotations

from flamerite_bt.device import Device

from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import PLATFORMS
from .coordinator import FlameriteConfigEntry, FlameriteDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: FlameriteConfigEntry) -> bool:
    """Set up Flamerite Fireplace from a config entry."""

    ble_device = bluetooth.async_ble_device_from_address(hass, entry.data[CONF_ADDRESS])
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Couldn't find a nearby Flamerite device for address: {
                entry.data[CONF_ADDRESS]
            }"
        )

    # Connect to the device.
    device = Device(ble_device)
    await device.connect(retry_attempts=4)
    if not device.is_connected:
        raise ConfigEntryNotReady(f"Failed to connect to: {device.mac}")

    # Create and wire the coordinator
    coordinator = FlameriteDataUpdateCoordinator(hass, entry, device)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FlameriteConfigEntry) -> bool:
    """Unload a config entry."""

    await entry.runtime_data.data.disconnect()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
