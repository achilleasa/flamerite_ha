"""Constants for the Flamerite Fireplace integration."""

from homeassistant.const import Platform

DOMAIN = "flamerite"
DEFAULT_NAME = "Flamerite"
DEVICE_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
UPDATE_INTERVAL_MS = 5000

PLATFORMS = [
    Platform.SWITCH,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.NUMBER,
]
