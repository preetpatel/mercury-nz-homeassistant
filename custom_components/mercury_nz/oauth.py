import aiohttp
import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from .const import TOKEN_STORAGE_KEY, TOKEN_STORAGE_VERSION

class TokenStore:
    def __init__(self, hass: HomeAssistant):
        self._store = Store(hass, TOKEN_STORAGE_VERSION, TOKEN_STORAGE_KEY)

    async def async_load(self):
        return await self._store.async_load() or {}

    async def async_save(self, data: dict):
        await self._store.async_save(data or {})

async def async_refresh_tokens(
    session: aiohttp.ClientSession,
    token_url: str,
    client_id: str,
    refresh_token: str,
    scope: str | None = None
) -> dict:
    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }
    if scope:
        payload["scope"] = scope

    async with async_timeout.timeout(30):
        async with session.post(token_url, data=payload) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Refresh failed ({resp.status}): {text}")
            return await resp.json()
