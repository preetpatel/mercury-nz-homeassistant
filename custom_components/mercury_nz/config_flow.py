from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, DEFAULT_TOKEN_URL
from .oauth import TokenStore

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("customer_id"): str,
    vol.Required("account_id"): str,
    vol.Required("service_id"): str,
    vol.Required("client_id"): str,
    vol.Required("api_subscription_key"): str,
    vol.Optional("scope"): str,
    vol.Optional("token_url", default=DEFAULT_TOKEN_URL): str,
    vol.Required("refresh_token"): str,
})

STEP_OPTIONS_SCHEMA = vol.Schema({
    vol.Optional("poll_minutes", default=15): int,
    vol.Optional("timezone"): str
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        store = TokenStore(self.hass)
        await store.async_save({"refresh_token": user_input.pop("refresh_token")})
        return self.async_create_entry(
            title=f"Mercury NZ ({user_input['customer_id']})",
            data=user_input,
            options={"poll_minutes": 15}
        )

    async def async_step_reauth(self, user_input=None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="reauth", data_schema=vol.Schema({
                vol.Required("refresh_token"): str
            }))
        store = TokenStore(self.hass)
        tokens = await store.async_load()
        tokens.update({"refresh_token": user_input["refresh_token"]})
        await store.async_save(tokens)
        return self.async_abort(reason="reauth_successful")

    async def async_step_options(self, user_input=None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="options", data_schema=STEP_OPTIONS_SCHEMA)
        return self.async_create_entry(title="", data=user_input)
