"""Support for ha_traccar sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
)
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
    """Set up sensor entities."""
    coordinator: TraccarServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    # 记录已创建的设备 ID，避免重复添加
    created_device_ids = set()

    def _create_entities():
        """Create sensor entities for devices in coordinator data."""
        if not coordinator.data:
            return

        entities = []
        for device_id, device_entry in coordinator.data.items():
            if device_id in created_device_ids:
                continue

            device = device_entry["device"]
            # 基础传感器（每个设备都有）
            entities.extend([
                TraccarServerBatterySensor(coordinator, device),
                TraccarServerAltitudeSensor(coordinator, device),
                TraccarServerSpeedSensor(coordinator, device),
                TraccarServerCourseSensor(coordinator, device),
                TraccarServerAddressSensor(coordinator, device),
                TraccarServerGeofenceSensor(coordinator, device),
            ])

            # 可选传感器（仅当属性存在时）
            attrs = device_entry["position"].get("attributes", {})
            if "deviceTemp" in attrs:
                entities.append(TraccarServerTemperatureSensor(coordinator, device))
            if "totalDistance" in attrs:
                entities.append(TraccarServerDistanceSensor(coordinator, device))

            created_device_ids.add(device_id)

        if entities:
            async_add_entities(entities)

    # 立即尝试创建（若已有数据）
    _create_entities()

    # 监听协调器数据变化，以便新设备出现时自动添加实体
    def _coordinator_update():
        _create_entities()

    entry.async_on_unload(coordinator.async_add_listener(_coordinator_update))


class TraccarServerBatterySensor(TraccarServerEntity, SensorEntity):
    """Represent a battery sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "battery")
        self._attr_translation_key = "battery"

    @property
    def native_value(self) -> int | None:
        """Return battery level as percentage."""
        level = self.traccar_attributes.get("batteryLevel")
        if level is None:
            return None
        return int(level)


class TraccarServerAltitudeSensor(TraccarServerEntity, SensorEntity):
    """Represent an altitude sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfLength.METERS

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "altitude")
        self._attr_translation_key = "altitude"

    @property
    def native_value(self) -> float:
        """Return altitude in meters."""
        return self.traccar_position.get("altitude", 0.0)


class TraccarServerSpeedSensor(TraccarServerEntity, SensorEntity):
    """Represent a speed sensor."""

    _attr_device_class = SensorDeviceClass.SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "speed")
        self._attr_translation_key = "speed"

    @property
    def native_value(self) -> float:
        """Return speed in km/h (Traccar returns knots)."""
        speed_knots = self.traccar_position.get("speed", 0.0)
        return speed_knots * 1.852  # 1 knot = 1.852 km/h


class TraccarServerCourseSensor(TraccarServerEntity, SensorEntity):
    """Represent a course sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°"

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "course")
        self._attr_translation_key = "course"

    @property
    def native_value(self) -> float:
        """Return course in degrees."""
        return self.traccar_position.get("course", 0.0)


class TraccarServerTemperatureSensor(TraccarServerEntity, SensorEntity):
    """Represent a temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "temperature")
        self._attr_translation_key = "temperature"

    @property
    def native_value(self) -> float:
        """Return temperature in Celsius."""
        return self.traccar_attributes.get("deviceTemp", 0.0)


class TraccarServerDistanceSensor(TraccarServerEntity, SensorEntity):
    """Represent a total distance sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "distance")
        self._attr_translation_key = "distance"

    @property
    def native_value(self) -> float:
        """Return total distance in kilometers."""
        meters = self.traccar_attributes.get("totalDistance", 0)
        return round(meters / 1000, 2)


class TraccarServerAddressSensor(TraccarServerEntity, SensorEntity):
    """Represent an address sensor."""

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "address")
        self._attr_translation_key = "address"

    @property
    def native_value(self) -> str | None:
        """Return address string."""
        addr = self.traccar_position.get("address")
        return addr if addr else None


class TraccarServerGeofenceSensor(TraccarServerEntity, SensorEntity):
    """Represent a geofence sensor."""

    def __init__(self, coordinator: TraccarServerCoordinator, device: dict) -> None:
        super().__init__(coordinator, device, "geofence")
        self._attr_translation_key = "geofence"

    @property
    def native_value(self) -> str | None:
        """Return geofence name."""
        geofence = self.traccar_geofence
        if geofence:
            return geofence.get("name")
        return None