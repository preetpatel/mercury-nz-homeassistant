from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import MercuryCoordinator

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: MercuryCoordinator = hass.data[entry.domain][entry.entry_id]
    async_add_entities([
        MercuryTotalConsumptionSensor(coordinator, entry),
        MercuryTotalCostSensor(coordinator, entry),
    ])

class BaseMercurySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: MercuryCoordinator, entry: ConfigEntry, name: str, unit: str | None):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{name}"
        self._attr_native_unit_of_measurement = unit

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        try:
            series = data["usage"][0]["data"]
        except Exception:
            series = []
        return {"hourly": series}

class MercuryTotalConsumptionSensor(BaseMercurySensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "Mercury Usage Total kWh", "kWh")

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        try:
            series = data["usage"][0]["data"]
            return round(sum(item.get("consumption") or 0 for item in series), 3)
        except Exception:
            return None

class MercuryTotalCostSensor(BaseMercurySensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "Mercury Usage Total Cost", "NZD")

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        try:
            series = data["usage"][0]["data"]
            return round(sum(item.get("cost") or 0 for item in series), 2)
        except Exception:
            return None
