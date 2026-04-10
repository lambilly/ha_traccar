"""The ha_traccar integration."""
from __future__ import annotations

from datetime import timedelta

from pytraccar import ApiClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_CUSTOM_ATTRIBUTES,
    CONF_EVENTS,
    CONF_MAX_ACCURACY,
    CONF_SKIP_ACCURACY_FILTER_FOR,
    DOMAIN,
    LOGGER,
)
from .coordinator import TraccarServerCoordinator

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ha_traccar from a config entry."""
    # 创建 HA 托管的 aiohttp 会话
    session = async_create_clientsession(
        hass,
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
    )

    # 创建 Traccar API 客户端
    client = ApiClient(
        host=entry.data[CONF_HOST],
        port=int(entry.data.get(CONF_PORT, 8082)),
        ssl=entry.data.get(CONF_SSL, False),
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
        client_session=session,
    )

    coordinator = TraccarServerCoordinator(
        hass=hass,
        config_entry=entry,
        client=client,
        events=entry.options.get(CONF_EVENTS, []),
        max_accuracy=entry.options.get(CONF_MAX_ACCURACY, 0.0),
        skip_accuracy_filter_for=entry.options.get(CONF_SKIP_ACCURACY_FILTER_FOR, []),
        custom_attributes=entry.options.get(CONF_CUSTOM_ATTRIBUTES, []),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        LOGGER.error("Failed to refresh coordinator: %s", ex)
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # 设置事件导入定时任务（仅当配置了事件时）
    if entry.options.get(CONF_EVENTS):
        # import_events 方法接受一个可选的 datetime 参数，直接传入即可
        entry.async_on_unload(
            async_track_time_interval(
                hass,
                coordinator.import_events,
                timedelta(seconds=30),
                cancel_on_shutdown=True,
                name="ha_traccar_import_events",
            )
        )

    # 启动 WebSocket 订阅（后台任务）
    entry.async_create_background_task(
        hass=hass,
        target=coordinator.subscribe(),
        name="ha_traccar subscription",
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)