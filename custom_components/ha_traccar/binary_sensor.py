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

    # 记录已创建的设备 ID，避免重复添加
    created_device_ids = set()

    def _create_entities():
        """Create binary sensor entities for devices in coordinator data."""
        if not coordinator.data:
            return

        entities = []
        for device_id, device_entry in coordinator.data.items():
            if device_id in created_device_ids:
                continue
            device = device_entry["device"]
            entities.append(TraccarServerMotionBinarySensor(coordinator, device))
            entities.append(TraccarServerStatusBinarySensor(coordinator, device))
            entities.append(TraccarServerChargingBinarySensor(coordinator, device))
            created_device_ids.add(device_id)

        if entities:
            async_add_entities(entities)

    # 立即尝试创建（若已有数据）
    _create_entities()

    # 监听协调器数据变化，以便新设备出现时自动添加实体
    def _coordinator_update():
        _create_entities()

    entry.async_on_unload(coordinator.async_add_listener(_coordinator_update))


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
        if "charge" in attrs:
            return bool(attrs["charge"])
        if "charging" in attrs:
            return bool(attrs["charging"])
        return bool(attrs.get("ignition", False))