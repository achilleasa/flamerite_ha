"""Color selection support for Flamerite devices."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from flamerite_bt.const import Color
from flamerite_bt.device import Device
from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (  # noqa: RUF100
    AddConfigEntryEntitiesCallback,
)

from .coordinator import FlameriteConfigEntry, FlameriteDataUpdateCoordinator
from .entity import FlameriteEntity

COLOR_NAME_MAP = {v.__str__(): v for v in Color}


@dataclass(frozen=True, kw_only=True)
class FlameriteSelectEntityDescription(SelectEntityDescription):
    """Describes a Flamerite select entity."""

    get_value_fn: Callable[[Device], Any]
    set_value_fn: Callable[[Device, Any], Coroutine[Any, Any, None]]


class FlameriteSelectEntity(FlameriteEntity, SelectEntity):  # type: ignore
    """A select entity for controlling the color of fireplace LEDs."""

    entity_description: FlameriteSelectEntityDescription

    def __init__(
        self,
        coordinator: FlameriteDataUpdateCoordinator,
        description: FlameriteSelectEntityDescription,
    ):
        """Initialize LED controller entity."""
        super().__init__(coordinator, description)
        self.entity_description = description  # type: ignore

    @property
    def current_option(self) -> str | None:  # type: ignore
        """Get the selected color."""
        return self.entity_description.get_value_fn(self.device).__str__()

    async def async_select_option(self, option: str) -> None:
        """Change the selected color."""
        color = COLOR_NAME_MAP[option]
        await self.entity_description.set_value_fn(self.device, color)
        await self.coordinator.async_request_refresh()


SELECT_DESCRS = [
    FlameriteSelectEntityDescription(
        key="flame_leds",
        translation_key="flame_leds",
        icon="mdi:fire",
        options=list(COLOR_NAME_MAP.keys()),
        get_value_fn=lambda device: device.flame_color,
        set_value_fn=lambda device, value: device.set_flame_color(value),
    ),
    FlameriteSelectEntityDescription(
        key="fuel_leds",
        translation_key="fuel_leds",
        icon="mdi:fuel",
        options=list(COLOR_NAME_MAP.keys()),
        get_value_fn=lambda device: device.fuel_color,
        set_value_fn=lambda device, value: device.set_fuel_color(value),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FlameriteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the select platform."""

    coordinator = config_entry.runtime_data
    entities = [
        FlameriteSelectEntity(coordinator, description)
        for description in SELECT_DESCRS
    ]
    async_add_entities(entities)
