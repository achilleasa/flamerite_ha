"""Base class definition for Flamerite entities."""

from flamerite_bt.device import Device
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FlameriteDataUpdateCoordinator


class FlameriteEntity(CoordinatorEntity[FlameriteDataUpdateCoordinator]):
    """Base class for Flamerite entities."""

    device: Device

    def __init__(
        self,
        coordinator: FlameriteDataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize Flamerite base entity."""
        super().__init__(coordinator)

        self.device = coordinator.data
        self._attr_unique_id = f"{self.device.serial_number}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.device.serial_number)},
            manufacturer=self.device.manufacturer,
            model=self.device.model_number,
            serial_number=self.device.serial_number,
            sw_version=self.device.firmware_revision,
            hw_version=self.device.hardware_revision,
            name=self.device.name,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_available = self.device.is_connected
        self.async_write_ha_state()
