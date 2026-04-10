"""Base entity for ha_traccar."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TraccarServerCoordinator
from .utils import sanitize_entity_id


class TraccarServerEntity(CoordinatorEntity[TraccarServerCoordinator]):
    """Base entity for ha_traccar."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TraccarServerCoordinator,
        device: dict,
        entity_type_suffix: str,
    ) -> None:
        """Initialize the ha_traccar entity."""
        super().__init__(coordinator)
        self.device_id = device["id"]
        self.entity_type_suffix = entity_type_suffix

        # 生成唯一 ID
        unique_id = device.get("uniqueId")
        if not unique_id:
            unique_id = f"unknown_{device['id']}"
        self._attr_unique_id = f"{unique_id}_{entity_type_suffix}" if entity_type_suffix else unique_id

        # 设备信息
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            model=device.get("model"),
            name=device["name"],
        )

        # 保存设备名和 sanitized 名称（用于某些实体生成 entity_id）
        self._device_name = device["name"]
        self._safe_name = device.get("safe_name", sanitize_entity_id(device["name"], device["id"]))

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.data is not None
            and self.device_id in self.coordinator.data
        )

    @property
    def traccar_device(self) -> dict | None:
        """Return the device dict, or None if not available."""
        if not self.available:
            return None
        return self.coordinator.data[self.device_id].get("device", {})

    @property
    def traccar_geofence(self) -> dict | None:
        """Return the geofence dict, or None."""
        if not self.available:
            return None
        return self.coordinator.data[self.device_id].get("geofence")

    @property
    def traccar_position(self) -> dict:
        """Return the position dict, or empty dict."""
        if not self.available:
            return {}
        return self.coordinator.data[self.device_id].get("position", {})

    @property
    def traccar_attributes(self) -> dict[str, Any]:
        """Return the attributes dict."""
        return self.traccar_position.get("attributes", {})

    async def async_added_to_hass(self) -> None:
        """Entity added to hass."""
        # 使用更具体的信号名称避免冲突
        signal = f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_{self.device_id}_update"
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal,
                self.async_write_ha_state,
            )
        )
        await super().async_added_to_hass()