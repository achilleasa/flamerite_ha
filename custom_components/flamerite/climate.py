"""Climate entity support for Flamerite devices."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from flamerite_bt.const import THERMOSTAT_MAX, THERMOSTAT_MIN, HeatMode
from flamerite_bt.device import Device

from homeassistant.components.climate.const import (
    FAN_HIGH,
    FAN_LOW,
    FAN_OFF,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,  # noqa: RUF100
)

from .coordinator import FlameriteConfigEntry, FlameriteDataUpdateCoordinator
from .entity import FlameriteEntity


@dataclass(frozen=True, kw_only=True)
class FlameriteClimateEntityDescription(ClimateEntityDescription):
    """Describes a Flamerite climate entity."""

    is_on_fn: Callable[[Device], bool]
    turn_on_fn: Callable[[Device], Coroutine[Any, Any, None]]
    get_heat_mode_fn: Callable[[Device], HeatMode]
    set_heat_mode_fn: Callable[
        [Device, HeatMode], Coroutine[Any, HeatMode, None]
    ]
    get_thermostat_fn: Callable[[Device], int]
    set_thermostat_fn: Callable[[Device, int], Coroutine[Any, int, None]]


class FlameriteClimateEntity(FlameriteEntity, ClimateEntity):  # type: ignore
    """A climate entity for controlling the fireplace heater."""

    entity_description: FlameriteClimateEntityDescription  # type: ignore

    def __init__(
        self,
        coordinator: FlameriteDataUpdateCoordinator,
        description: FlameriteClimateEntityDescription,
    ):
        """Initialize fireplace climate entity."""
        super().__init__(coordinator, description)
        self.entity_description = description  # type: ignore

        self._attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
        )
        self._attr_hvac_modes = [
            HVACMode.HEAT,
            HVACMode.OFF,
        ]
        self._attr_fan_modes = [FAN_OFF, FAN_LOW, FAN_HIGH]
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = THERMOSTAT_MIN
        self._attr_max_temp = THERMOSTAT_MAX
        self._attr_target_temperature_step = 1.0

    @property
    def hvac_mode(self) -> HVACMode | None:  # type: ignore
        """Return currently active HVAC mode."""
        if (
            self.entity_description.get_heat_mode_fn(self.device)
            is HeatMode.OFF
        ):
            return HVACMode.OFF
        return HVACMode.HEAT

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the current HVAC mode."""
        heat_mode = self.entity_description.get_heat_mode_fn(self.device)

        if hvac_mode is HVACMode.HEAT:
            # The device must be on to enable any heat mode
            if not self.entity_description.is_on_fn(self.device):
                await self.entity_description.turn_on_fn(self.device)

            # If heating is curently off, switch to low heat mode; otherwise
            # retain existing heat mode.
            if heat_mode is HeatMode.OFF:
                heat_mode = HeatMode.LOW
        else:
            heat_mode = HeatMode.OFF

        await self.entity_description.set_heat_mode_fn(self.device, heat_mode)
        await self.coordinator.async_request_refresh()

    @property
    def target_temperature(self) -> float | None:  # type: ignore
        """Return the thermostat setting."""
        return self.entity_description.get_thermostat_fn(self.device)

    async def async_set_temperature(self, **kwargs):
        """Set the thermostat setting."""
        temperature = kwargs[ATTR_TEMPERATURE]
        await self.entity_description.set_thermostat_fn(
            self.device, int(temperature)
        )
        await self.coordinator.async_request_refresh()

    @property
    def fan_mode(self) -> str | None:  # type: ignore
        """Return the current fan mode."""
        heat_mode = self.entity_description.get_heat_mode_fn(self.device)
        if heat_mode is HeatMode.LOW:
            return FAN_LOW
        if heat_mode is HeatMode.HIGH:
            return FAN_HIGH
        return FAN_OFF

    async def async_set_fan_mode(self, fan_mode: str):
        """Set new target fan mode."""
        heat_mode = HeatMode.OFF

        if fan_mode in [FAN_LOW, FAN_HIGH]:
            # The device must be on to adjust the fan.
            if not self.entity_description.is_on_fn(self.device):
                await self.entity_description.turn_on_fn(self.device)

            heat_mode = HeatMode.LOW if fan_mode == FAN_LOW else HeatMode.HIGH

        await self.entity_description.set_heat_mode_fn(self.device, heat_mode)
        await self.coordinator.async_request_refresh()


CLIMATE_DESCRS = [
    FlameriteClimateEntityDescription(
        key="heater",
        translation_key="heater",
        icon="mdi:radiator",
        is_on_fn=lambda dev: dev.is_powered_on,
        turn_on_fn=lambda dev: dev.set_powered_on(True),
        get_heat_mode_fn=lambda dev: dev.heat_mode,
        set_heat_mode_fn=lambda dev, mode: dev.set_heat_mode(mode),
        get_thermostat_fn=lambda dev: dev.thermostat,
        set_thermostat_fn=lambda dev, val: dev.set_thermostat(val),
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FlameriteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the climate platform."""

    coordinator = config_entry.runtime_data
    entities = [
        FlameriteClimateEntity(coordinator, description)
        for description in CLIMATE_DESCRS
    ]
    async_add_entities(entities)
