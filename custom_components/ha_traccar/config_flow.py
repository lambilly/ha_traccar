"""Config flow for ha_traccar integration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaOptionsFlowHandler,
)
from homeassistant.helpers.selector import (
    BooleanSelector,
    BooleanSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CUSTOM_ATTRIBUTES,
    CONF_EVENTS,
    CONF_MAX_ACCURACY,
    CONF_SKIP_ACCURACY_FILTER_FOR,
    DOMAIN,
    EVENTS,
    LOGGER,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Optional(CONF_PORT, default="8082"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL)
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_SSL, default=False): BooleanSelector(BooleanSelectorConfig()),
        vol.Optional(CONF_VERIFY_SSL, default=True): BooleanSelector(
            BooleanSelectorConfig()
        ),
    }
)

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(
        schema=vol.Schema(
            {
                vol.Optional(CONF_MAX_ACCURACY, default=0.0): NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0.0,
                    )
                ),
                vol.Optional(CONF_CUSTOM_ATTRIBUTES, default=[]): SelectSelector(
                    SelectSelectorConfig(
                        mode=SelectSelectorMode.DROPDOWN,
                        multiple=True,
                        sort=True,
                        custom_value=True,
                        options=[],
                    )
                ),
                vol.Optional(CONF_SKIP_ACCURACY_FILTER_FOR, default=[]): SelectSelector(
                    SelectSelectorConfig(
                        mode=SelectSelectorMode.DROPDOWN,
                        multiple=True,
                        sort=True,
                        custom_value=True,
                        options=[],
                    )
                ),
                vol.Optional(CONF_EVENTS, default=[]): SelectSelector(
                    SelectSelectorConfig(
                        mode=SelectSelectorMode.DROPDOWN,
                        multiple=True,
                        sort=True,
                        custom_value=True,
                        options=list(EVENTS.keys()),
                    )
                ),
            }
        )
    ),
}


class TraccarServerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ha_traccar."""

    VERSION = 1

    async def _test_connection(self, user_input: dict[str, Any]) -> tuple[bool, str | None]:
        """Test connection and authentication.
        
        Returns (success, error_code).
        """
        host = user_input[CONF_HOST]
        port = int(user_input.get(CONF_PORT, 8082))
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        verify_ssl = user_input.get(CONF_VERIFY_SSL, True)
        ssl = user_input.get(CONF_SSL, False)

        session = async_get_clientsession(self.hass, verify_ssl=verify_ssl)
        scheme = "https" if ssl else "http"
        base_url = f"{scheme}://{host}:{port}"
        login_url = f"{base_url}/api/session"

        data = {"email": username, "password": password}
        try:
            async with session.post(login_url, data=data) as resp:
                if resp.status == 200:
                    return True, None
                elif resp.status == 401:
                    return False, "invalid_auth"
                else:
                    text = await resp.text()
                    LOGGER.debug("Traccar login failed: %s - %s", resp.status, text)
                    return False, "cannot_connect"
        except aiohttp.ClientConnectionError:
            return False, "cannot_connect"
        except aiohttp.ClientError as ex:
            LOGGER.debug("Traccar connection error: %s", ex)
            return False, "cannot_connect"
        except Exception:
            LOGGER.exception("Unexpected exception during connection test")
            return False, "unknown"

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # 检查是否已存在相同主机和端口的配置（考虑 SSL 状态）
            self._async_abort_entries_match(
                {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_SSL: user_input.get(CONF_SSL, False),
                }
            )

            success, error_code = await self._test_connection(user_input)
            if success:
                return self.async_create_entry(
                    title=f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}",
                    data=user_input,
                )
            errors["base"] = error_code or "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_import(
        self, import_info: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Import from YAML."""
        configured_port = str(import_info[CONF_PORT])

        self._async_abort_entries_match(
            {
                CONF_HOST: import_info[CONF_HOST],
                CONF_PORT: configured_port,
                CONF_SSL: import_info.get(CONF_SSL, False),
            }
        )

        # 测试连接，失败则放弃导入
        success, error_code = await self._test_connection(dict(import_info))
        if not success:
            LOGGER.error(
                "Failed to import Traccar configuration for %s:%s: %s",
                import_info[CONF_HOST],
                configured_port,
                error_code,
            )
            return self.async_abort(reason=error_code or "cannot_connect")

        # 处理事件导入
        if "all_events" in (imported_events := import_info.get("event", [])):
            events = list(EVENTS.values())
        else:
            events = imported_events

        return self.async_create_entry(
            title=f"{import_info[CONF_HOST]}:{configured_port}",
            data={
                CONF_HOST: import_info[CONF_HOST],
                CONF_PORT: configured_port,
                CONF_SSL: import_info.get(CONF_SSL, False),
                CONF_VERIFY_SSL: import_info.get(CONF_VERIFY_SSL, True),
                CONF_USERNAME: import_info[CONF_USERNAME],
                CONF_PASSWORD: import_info[CONF_PASSWORD],
            },
            options={
                CONF_MAX_ACCURACY: import_info[CONF_MAX_ACCURACY],
                CONF_EVENTS: events,
                CONF_CUSTOM_ATTRIBUTES: import_info.get("monitored_conditions", []),
                CONF_SKIP_ACCURACY_FILTER_FOR: import_info.get(
                    "skip_accuracy_filter_on", []
                ),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SchemaOptionsFlowHandler:
        """Return options flow."""
        return SchemaOptionsFlowHandler(config_entry, OPTIONS_FLOW)