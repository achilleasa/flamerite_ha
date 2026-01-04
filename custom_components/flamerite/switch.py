"""Switch support for Flamerite devices."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
import time
from typing import Any

from flamerite_bt.device import Device

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,  # noqa: RUF100
)

from .coordinator import FlameriteConfigEntry, FlameriteDataUpdateCoordinator
from .entity import FlameriteEntity


@dataclass(frozen=True, kw_only=True)
class FlameriteSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Flamerite switch entity."""

    is_on_fn: Callable[[Device], bool]
    turn_on_fn: Callable[[Device], Coroutine[Any, Any, None]]
    turn_off_fn: Callable[[Device], Coroutine[Any, Any, None]]


class FlameriteSwitchEntity(FlameriteEntity, SwitchEntity):  # type: ignore
    """A switch entity."""

    entity_description: FlameriteSwitchEntityDescription
    _off_delay_until: float | None = None

    # Seconds to wait while the device transitions from on -> off after
    # sending the turn off command before reporting the actual device state.
    _off_delay_seconds: float = 7.0

    def __init__(
        self,
        coordinator: FlameriteDataUpdateCoordinator,
        description: FlameriteSwitchEntityDescription,
    ):
        """Initialize switch entity."""
        super().__init__(coordinator, description)
        self.entity_description = description  # type: ignore

    @property
    def is_on(self) -> bool | None:  # type: ignore
        """Return True if the switch is on."""
        if self._off_delay_until and time.monotonic() < self._off_delay_until:
            # Still in delayed-off window; show the device as off
            return False

        return self.entity_description.is_on_fn(self.device)

    async def async_turn_on(self, **kwargs):
        """Turn the fireplace on."""
        await self.entity_description.turn_on_fn(self.device)
        self._off_delay_until = None
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the fireplace off."""
        # The fireplace takes some time to turn down after receiving the power
        # off command. During this time, the device reports its state as 'on'
        # and this causes the switch state to jump from off -> on -> off. To
        # avoid this we force the reported device state as off for the
        # transition duration.
        await self.entity_description.turn_off_fn(self.device)
        self._off_delay_until = time.monotonic() + self._off_delay_seconds
        self._attr_is_on = False
        self.async_write_ha_state()


SWITCH_DESCRS = [
    FlameriteSwitchEntityDescription(
        key="power_state",
        translation_key="power_state",
        icon="mdi:power",
        device_class=SwitchDeviceClass.SWITCH,
        is_on_fn=lambda dev: dev.is_powered_on,
        turn_on_fn=lambda dev: dev.set_powered_on(True),
        turn_off_fn=lambda dev: dev.set_powered_on(False),
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: FlameriteConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switch platform."""

    coordinator = config_entry.runtime_data
    entities = [
        FlameriteSwitchEntity(coordinator, description)
        for description in SWITCH_DESCRS
    ]
    async_add_entities(entities)
