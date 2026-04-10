"""Config flow for ha_traccar integration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pytraccar import ApiClient, ServerModel, TraccarException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
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

# 关键：只保留 host、port、token，没有 username/password
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Optional(CONF_PORT, default="8082"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Required("token"): TextSelector(
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
                        options=list(EVENTS),
                    )
                ),
            }
        )
    ),
}


class TraccarServerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ha_traccar."""

    async def _get_server_info(self, user_input: dict[str, Any]) -> ServerModel:
        """Connect to Traccar server using API token."""
        host = user_input[CONF_HOST]
        port = int(user_input.get(CONF_PORT, 8082))
        token = user_input["token"]
        verify_ssl = user_input.get(CONF_VERIFY_SSL, True)
        ssl = user_input.get(CONF_SSL, False)

        session = async_get_clientsession(self.hass)

        # 只使用 token，不传 username/password
        client = ApiClient(
            host=host,
            port=port,
            token=token,
            client_session=session,
            ssl=ssl,
            verify_ssl=verify_ssl,
        )
        return await client.get_server()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match(
                {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                }
            )

            try:
                await self._get_server_info(user_input)
            except TraccarException as exception:
                LOGGER.error("Unable to connect to Traccar: %s", exception)
                errors["base"] = "cannot_connect"
            except Exception:
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}",
                    data=user_input,
                )

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
            }
        )

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
                "token": import_info["token"],
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