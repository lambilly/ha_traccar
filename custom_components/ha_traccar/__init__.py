"""The ha_traccar integration."""
from __future__ import annotations

from datetime import timedelta
import re

from aiohttp import CookieJar
from pytraccar import ApiClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
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
)
from .coordinator import TraccarServerCoordinator

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]

def format_entity_id(entity_id_format: str, name: str) -> str:
    """Format the entity ID."""
    name = re.sub(r'[^\w\s]', '', name).lower()
    return entity_id_format.format(name)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ha_traccar from a config entry."""
    client_session = async_create_clientsession(
        hass,
        cookie_jar=CookieJar(
            unsafe=not entry.data[CONF_SSL] or not entry.data[CONF_VERIFY_SSL]
        ),
    )
    
    # 使用 token 认证
    client = ApiClient(
        host=entry.data[CONF_HOST],
        port=int(entry.data[CONF_PORT]),
        token=entry.data["token"],
        client_session=client_session,
        ssl=entry.data[CONF_SSL],
        verify_ssl=entry.data[CONF_VERIFY_SSL],
    )
    
    coordinator = TraccarServerCoordinator(
        hass=hass,
        client=client,
        events=entry.options.get(CONF_EVENTS, []),
        max_accuracy=entry.options.get(CONF_MAX_ACCURACY, 0.0),
        skip_accuracy_filter_for=entry.options.get(CONF_SKIP_ACCURACY_FILTER_FOR, []),
        custom_attributes=entry.options.get(CONF_CUSTOM_ATTRIBUTES, []),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    if entry.options.get(CONF_EVENTS):
        entry.async_on_unload(
            async_track_time_interval(
                hass,
                coordinator.import_events,
                timedelta(seconds=30),
                cancel_on_shutdown=True,
                name="ha_traccar_import_events",
            )
        )

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
    """Handle an options update."""
    await hass.config_entries.async_reload(entry.entry_id)