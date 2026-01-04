"""Config flow for the Flamerite Fireplace integration."""

from __future__ import annotations

import asyncio
from typing import Any

from flamerite_bt.device import Device
import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN


class FlameriteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Flamerite Fireplace."""

    VERSION = 1
    _pair_task: asyncio.Task | None = None

    def __init__(self) -> None:
        """Initialize config flow."""
        self._discovered_address: str
        self._pairing_address: str

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step triggered by a user."""
        return await self.async_step_select_device()

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to select a device."""
        # User selected a device from the list
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(
                format_mac(address), raise_on_progress=False
            )
            return await self.async_step_pair({CONF_ADDRESS: address})

        # Discover Flamerite devices that have not already been configured.
        flamerite_addresses: set[str] = set()
        configured_addresses = self._async_current_ids(include_ignore=False)
        all_discovered_devices = bluetooth.async_discovered_service_info(
            self.hass, connectable=True
        )

        for disc_info in all_discovered_devices:
            address = disc_info.address
            if (
                address in configured_addresses
                or address in flamerite_addresses
            ):
                continue

            # Check for supported devices
            if not disc_info.advertisement or not Device.is_supported_device(
                disc_info.advertisement
            ):
                continue
            flamerite_addresses.add(address)

        # Check if no compatible devices were found
        if not flamerite_addresses:
            return self.async_abort(reason="no_devices_found")

        # Display device picker and run the step again after the user has
        # selected a device.
        picker_opts = {addr: addr for addr in flamerite_addresses}

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(picker_opts)}
            ),
        )

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user-confirmation of discovered device."""

        if user_input is not None:
            return await self.async_step_pair(
                {CONF_ADDRESS: self._discovered_address}
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"address": self._discovered_address},
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Wait until Flamerite device is paired and we can connect to it."""
        if user_input is not None:
            self._pairing_address = user_input[CONF_ADDRESS]

        address = self._pairing_address

        pair_task = self._pair_task
        if not pair_task:
            # Get ble device handle for the selected address
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, address
            )
            if not ble_device:
                return self.async_abort(
                    reason="device_no_longer_present",
                    description_placeholders={"address": address},
                )

            # Create NITRA device and attempt to connect. This will fail until
            # the user clicks the # pair/link button on the physical device.
            device = Device(ble_device)
            pair_task = self.hass.async_create_task(
                device.connect(retry_attempts=20)
            )
            self._pair_task = pair_task

        # We are still trying to pair.
        if not pair_task.done():
            return self.async_show_progress(
                step_id="pair",
                progress_action="pairing",
                description_placeholders={"address": address},
                progress_task=pair_task,
            )

        # Pairing task has completed; check result
        try:
            pair_task.result()
            return self.async_show_progress_done(
                next_step_id="pairing_complete"
            )
        except asyncio.exceptions.CancelledError:
            return self.async_abort(
                reason="pairing_failed",
                description_placeholders={"address": address},
            )

    async def async_step_pairing_complete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Paired to a Flamerite device and now create config entry."""
        return self.async_create_entry(
            title=self._pairing_address,
            data={
                CONF_ADDRESS: self._pairing_address,
            },
        )
