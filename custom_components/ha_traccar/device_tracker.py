"""Support for ha_traccar device tracking."""
from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_ADDRESS,
    ATTR_ALTITUDE,
    ATTR_CATEGORY,
    ATTR_GEOFENCE,
    ATTR_MOTION,
    ATTR_SPEED,
    ATTR_STATUS,
    ATTR_TRACCAR_ID,
    ATTR_TRACKER,
    DOMAIN,
)
from .coord_transform import gcj02_to_wgs84
from .coordinator import TraccarServerCoordinator
from .entity import TraccarServerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker entities."""
    coordinator: TraccarServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # ⚠️ 不再因为没数据就 return，避免实体不创建
    if coordinator.data:
        for device_entry in coordinator.data.values():
            device = device_entry["device"]
            entities.append(TraccarServerDeviceTracker(coordinator, device))
            entities.append(TraccarServerWGS84DeviceTracker(coordinator, device))

    async_add_entities(entities)


# ========================= 原始坐标 =========================
class TraccarServerDeviceTracker(TraccarServerEntity, TrackerEntity):
    """Represent a tracked device (original coordinates)."""

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "")
        self._attr_translation_key = "tracker"

    @property
    def battery_level(self) -> int | None:
        """Return battery value of the device."""
        level = (
            self.traccar_attributes.get("batteryLevel")
            or self.traccar_attributes.get("battery")
        )
        return int(level) if level is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific attributes."""
        geofence = self.traccar_geofence
        geofence_name = geofence.get("name") if geofence else None

        # speed 转 km/h（Traccar 默认是 knots）
        speed = self.traccar_position.get("speed")
        speed_kmh = speed * 1.852 if speed is not None else None

        return {
            **self.traccar_attributes,
            ATTR_ADDRESS: self.traccar_position.get("address"),
            ATTR_ALTITUDE: self.traccar_position.get("altitude"),
            ATTR_CATEGORY: self.traccar_device.get("category") if self.traccar_device else None,
            ATTR_GEOFENCE: geofence_name,
            ATTR_MOTION: self.traccar_attributes.get("motion", False),
            ATTR_SPEED: speed_kmh,
            ATTR_STATUS: self.traccar_device.get("status") if self.traccar_device else None,
            ATTR_TRACCAR_ID: self.traccar_device.get("id") if self.traccar_device else None,
            ATTR_TRACKER: DOMAIN,
        }

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        lat = self.traccar_position.get("latitude")
        return lat

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        lon = self.traccar_position.get("longitude")
        return lon

    @property
    def location_accuracy(self) -> int:
        """Return the gps accuracy of the device."""
        return self.traccar_position.get("accuracy", 0)

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS


# ========================= WGS84 坐标 =========================
class TraccarServerWGS84DeviceTracker(TraccarServerEntity, TrackerEntity):
    """Represent a tracked device with WGS84 coordinates."""

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "wgs84")
        self._attr_translation_key = "tracker_wgs84"

    @property
    def battery_level(self) -> int | None:
        """Return battery value of the device."""
        level = (
            self.traccar_attributes.get("batteryLevel")
            or self.traccar_attributes.get("battery")
        )
        return int(level) if level is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific attributes including original coordinates."""
        geofence = self.traccar_geofence
        geofence_name = geofence.get("name") if geofence else None

        lon = self.traccar_position.get("longitude")
        lat = self.traccar_position.get("latitude")

        if lon is None or lat is None:
            return {}

        lng, lat = gcj02_to_wgs84(lon, lat)

        # speed 转 km/h
        speed = self.traccar_position.get("speed")
        speed_kmh = speed * 1.852 if speed is not None else None

        return {
            **self.traccar_attributes,
            ATTR_ADDRESS: self.traccar_position.get("address"),
            ATTR_ALTITUDE: self.traccar_position.get("altitude"),
            ATTR_CATEGORY: self.traccar_device.get("category") if self.traccar_device else None,
            ATTR_GEOFENCE: geofence_name,
            ATTR_MOTION: self.traccar_attributes.get("motion", False),
            ATTR_SPEED: speed_kmh,
            ATTR_STATUS: self.traccar_device.get("status") if self.traccar_device else None,
            ATTR_TRACCAR_ID: self.traccar_device.get("id") if self.traccar_device else None,
            ATTR_TRACKER: DOMAIN,
            "wgs84_longitude": lng,
            "wgs84_latitude": lat,
        }

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device in WGS84."""
        lon = self.traccar_position.get("longitude")
        lat = self.traccar_position.get("latitude")

        if lon is None or lat is None:
            return None

        _, lat = gcj02_to_wgs84(lon, lat)
        return lat if lat != 0 else None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device in WGS84."""
        lon = self.traccar_position.get("longitude")
        lat = self.traccar_position.get("latitude")

        if lon is None or lat is None:
            return None

        lng, _ = gcj02_to_wgs84(lon, lat)
        return lng if lng != 0 else None

    @property
    def location_accuracy(self) -> int:
        """Return the gps accuracy of the device."""
        return self.traccar_position.get("accuracy", 0)

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS