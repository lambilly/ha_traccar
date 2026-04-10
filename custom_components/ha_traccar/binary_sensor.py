"""Support for ha_traccar binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TraccarServerCoordinator
from .entity import TraccarServerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator: TraccarServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    if not coordinator.data:
        return

    entities = []
    for device_entry in coordinator.data.values():
        device = device_entry["device"]
        entities.append(TraccarServerMotionBinarySensor(coordinator, device))
        entities.append(TraccarServerStatusBinarySensor(coordinator, device))
        entities.append(TraccarServerChargingBinarySensor(coordinator, device))

    async_add_entities(entities)


class TraccarServerMotionBinarySensor(TraccarServerEntity, BinarySensorEntity):
    """Represent a motion binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "motion")
        self._attr_translation_key = "motion"

    @property
    def is_on(self) -> bool:
        """Return true if motion is detected."""
        return self.traccar_attributes.get("motion", False)


class TraccarServerStatusBinarySensor(TraccarServerEntity, BinarySensorEntity):
    """Represent a status (online/offline) binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "status")
        self._attr_translation_key = "status"

    @property
    def is_on(self) -> bool:
        """Return true if device is online."""
        device = self.traccar_device
        if device is None:
            return False
        return device.get("status") == "online"


class TraccarServerChargingBinarySensor(TraccarServerEntity, BinarySensorEntity):
    """Represent a charging binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "charging")
        self._attr_translation_key = "charging"

    @property
    def is_on(self) -> bool:
        """Return true if device is charging."""
        attrs = self.traccar_attributes
        # 优先使用标准字段
        if "charge" in attrs:
            return bool(attrs["charge"])
        if "charging" in attrs:
            return bool(attrs["charging"])
        # 部分设备用 ignition 表示充电/点火状态
        return bool(attrs.get("ignition", False))