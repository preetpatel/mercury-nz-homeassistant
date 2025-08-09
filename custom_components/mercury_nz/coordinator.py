from __future__ import annotations
import datetime as dt
import logging
from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util
from .const import BASE_API, DOMAIN
from .oauth import async_refresh_tokens, TokenStore

_LOGGER = logging.getLogger(__name__)

class MercuryClient:
    def __init__(self, session: ClientSession, base_url: str, token_getter, api_subscription_key: str):
        self._session = session
        self._base = base_url
        self._get_token = token_getter
        self._api_subscription_key = api_subscription_key

    async def get_hourly_usage(self, customer_id, account_id, service_id, start_date, end_date):
        url = f"{self._base}/customers/{customer_id}/accounts/{account_id}/services/electricity/{service_id}/usage"
        params = {"interval": "hourly", "startDate": start_date, "endDate": end_date}
        headers = {
            "Authorization": f"Bearer {self._get_token()}",
            "Ocp-Apim-Subscription-Key": self._api_subscription_key
        }
        async with self._session.get(url, params=params, headers=headers) as resp:
            if resp.status == 401:
                raise PermissionError("Access token expired or invalid")
            if resp.status != 200:
                raise UpdateFailed(f"{resp.status}: {await resp.text()}")
            return await resp.json()

class MercuryCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry):
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=dt.timedelta(minutes=entry.options.get("poll_minutes", 15))
        )
        self.entry = entry
        self.store = TokenStore(hass)
        self.session: ClientSession = async_get_clientsession(hass)
        self._tokens: dict | None = None
        api_key = entry.data.get("api_subscription_key")
        if not api_key:
            raise UpdateFailed("API Subscription Key is required")
        self.client = MercuryClient(self.session, BASE_API, self._get_access_token, api_key)

    def _get_access_token(self) -> str:
        return self._tokens.get("access_token", "")

    async def _ensure_tokens(self):
        if self._tokens is None:
            self._tokens = await self.store.async_load()
        
        # If we have a refresh token but no access token, refresh to get one
        if self._tokens and "refresh_token" in self._tokens and "access_token" not in self._tokens:
            await self._refresh_and_save()
        elif not self._tokens or "refresh_token" not in self._tokens:
            raise UpdateFailed("No tokens available. Reauthenticate in options.")

    async def _refresh_and_save(self):
        from .const import DEFAULT_TOKEN_URL, DEFAULT_CLIENT_ID, DEFAULT_SCOPE
        data = await async_refresh_tokens(
            self.session,
            self.entry.data.get("token_url", DEFAULT_TOKEN_URL),
            self.entry.data.get("client_id", DEFAULT_CLIENT_ID),
            self._tokens["refresh_token"],
            self.entry.data.get("scope", DEFAULT_SCOPE)
        )
        self._tokens.update({
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", self._tokens["refresh_token"]),
            "expires_in": data.get("expires_in"),
            "obtained_at": dt_util.utcnow().isoformat()
        })
        await self.store.async_save(self._tokens)

    async def _async_update_data(self):
        await self._ensure_tokens()
        # Get current time - Home Assistant handles timezone internally
        now = dt_util.now()
        # API has 48-hour delay - fetch data from 2 days ago
        # Format dates with time and NZ timezone for proper API response
        start_date = (now - dt.timedelta(days=2)).date()
        end_date = (now - dt.timedelta(days=1)).date()
        start = f"{start_date.isoformat()}T00:00:00+12:00"
        end = f"{end_date.isoformat()}T00:00:00+12:00"
        try:
            return await self.client.get_hourly_usage(
                self.entry.data["customer_id"],
                self.entry.data["account_id"],
                self.entry.data["service_id"],
                start,
                end
            )
        except PermissionError:
            await self._refresh_and_save()
            return await self.client.get_hourly_usage(
                self.entry.data["customer_id"],
                self.entry.data["account_id"],
                self.entry.data["service_id"],
                start,
                end
            )
