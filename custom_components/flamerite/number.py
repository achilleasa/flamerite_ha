"""Color Numberion support for Flamerite devices."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from flamerite_bt.const import BRIGHTNESS_MAX, BRIGHTNESS_MIN
from flamerite_bt.device import Device

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,  # noqa: RUF100
)

from .coordinator import FlameriteConfigEntry, FlameriteDataUpdateCoordinator
from .entity import FlameriteEntity


@dataclass(frozen=True, kw_only=True)
class FlameriteNumberEntityDescription(NumberEntityDescription):
    """Describes a Flamerite Number entity."""

    get_value_fn: Callable[[Device], Any]
    set_value_fn: Callable[[Device, Any], Coroutine[Any, Any, None]]


class FlameriteNumberEntity(FlameriteEntity, NumberEntity):  # type: ignore
    """A Number entity for controlling the brightness of fireplace LEDs."""

    entity_description: FlameriteNumberEntityDescription

    def __init__(
        self,
        coordinator: FlameriteDataUpdateCoordinator,
        description: FlameriteNumberEntityDescription,
    ):
        """Initialize LED controller entity."""
        super().__init__(coordinator, description)
        self.entity_description = description  # type: ignore

    @property
    def native_value(self) -> float | None:  # type: ignore
        """Get the brightnesss value."""
        return float(self.entity_description.get_value_fn(self.device))

    async def async_set_native_value(self, value: float) -> None:
        """Change the brightness value."""
        await self.entity_description.set_value_fn(self.device, int(value))
        await self.coordinator.async_request_refresh()


Number_DESCRS = [
    FlameriteNumberEntityDescription(
        key="flame_brightness",
        translation_key="flame_brightness",
        icon="mdi:brightness-6",
        native_min_value=float(BRIGHTNESS_MIN),
        native_max_value=float(BRIGHTNESS_MAX),
        native_step=1.0,
        mode=NumberMode.SLIDER,
        get_value_fn=lambda device: device.flame_brightness,
        set_value_fn=lambda device, value: device.set_flame_brightness(value),
    ),
    FlameriteNumberEntityDescription(
        key="fuel_brightness",
        translation_key="fuel_brightness",
        icon="mdi:brightness-6",
        native_min_value=float(BRIGHTNESS_MIN),
        native_max_value=float(BRIGHTNESS_MAX),
        native_step=1.0,
        mode=NumberMode.SLIDER,
        get_value_fn=lambda device: device.fuel_brightness,
        set_value_fn=lambda device, value: device.set_fuel_brightness(value),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FlameriteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Number platform."""

    coordinator = config_entry.runtime_data
    entities = [
        FlameriteNumberEntity(coordinator, description)
        for description in Number_DESCRS
    ]
    async_add_entities(entities)
