from __future__ import annotations
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from .coordinator import MercuryCoordinator

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: MercuryCoordinator = hass.data[entry.domain][entry.entry_id]
    async_add_entities([
        MercuryEnergyConsumptionSensor(coordinator, entry),
        MercuryEnergyCostSensor(coordinator, entry),
    ])

class MercuryEnergyConsumptionSensor(RestoreEntity, CoordinatorEntity, SensorEntity):
    """Cumulative energy consumption sensor for Energy Dashboard."""
    
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "kWh"
    _attr_name = "Mercury Energy Consumption"
    _attr_icon = "mdi:lightning-bolt"
    
    def __init__(self, coordinator: MercuryCoordinator, entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_energy_consumption"
        self._cumulative_total = 0.0
        self._last_processed_date = None
        
    @property
    def native_value(self):
        """Return cumulative total energy consumption."""
        if not self.coordinator.data:
            return self._cumulative_total
            
        try:
            hourly_data = self.coordinator.data["usage"][0]["data"]
            if hourly_data:
                # Extract date from first entry (e.g., "2025-08-07T00:00:00")
                # All 24 entries are from the same day
                current_date = hourly_data[0]["date"][:10] if "date" in hourly_data[0] else None
                
                # Only add if this is a new day's data
                if current_date and current_date != self._last_processed_date:
                    # Sum all 24 hours of consumption for the complete day
                    daily_total = sum(item.get("consumption", 0) for item in hourly_data)
                    if daily_total > 0:  # Only add if we have valid data
                        self._cumulative_total += daily_total
                        self._last_processed_date = current_date
                    
        except (KeyError, IndexError, TypeError):
            pass
            
        return round(self._cumulative_total, 3)
    
    @property
    def extra_state_attributes(self):
        """Include the full 24-hour breakdown as attributes."""
        if not self.coordinator.data:
            return {}
            
        try:
            hourly_data = self.coordinator.data["usage"][0]["data"]
            daily_total = sum(item.get("consumption", 0) for item in hourly_data)
            
            return {
                "hourly_breakdown": hourly_data,
                "last_update_date": self._last_processed_date,
                "daily_total_kwh": round(daily_total, 3),
                "measurement_date": hourly_data[0]["date"][:10] if hourly_data and "date" in hourly_data[0] else None
            }
        except (KeyError, IndexError, TypeError):
            return {}
            
    async def async_added_to_hass(self):
        """Restore last known state when added to hass."""
        await super().async_added_to_hass()
        
        # Restore the last known state
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._cumulative_total = float(last_state.state)
                if last_state.attributes:
                    self._last_processed_date = last_state.attributes.get("last_update_date")
            except (ValueError, TypeError):
                pass

class MercuryEnergyCostSensor(RestoreEntity, CoordinatorEntity, SensorEntity):
    """Cumulative energy cost sensor for Energy Dashboard."""
    
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "NZD"
    _attr_name = "Mercury Energy Cost"
    _attr_icon = "mdi:currency-usd"
    
    def __init__(self, coordinator: MercuryCoordinator, entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_energy_cost"
        self._cumulative_cost = 0.0
        self._last_processed_date = None
        
    @property
    def native_value(self):
        """Return cumulative total energy cost."""
        if not self.coordinator.data:
            return self._cumulative_cost
            
        try:
            hourly_data = self.coordinator.data["usage"][0]["data"]
            if hourly_data:
                # Extract date from first entry
                current_date = hourly_data[0]["date"][:10] if "date" in hourly_data[0] else None
                
                # Only add if this is a new day's data
                if current_date and current_date != self._last_processed_date:
                    # Sum all 24 hours of cost for the complete day
                    daily_cost = sum(item.get("cost", 0) for item in hourly_data)
                    if daily_cost > 0:  # Only add if we have valid data
                        self._cumulative_cost += daily_cost
                        self._last_processed_date = current_date
                    
        except (KeyError, IndexError, TypeError):
            pass
            
        return round(self._cumulative_cost, 2)
    
    @property
    def extra_state_attributes(self):
        """Include the full 24-hour cost breakdown as attributes."""
        if not self.coordinator.data:
            return {}
            
        try:
            hourly_data = self.coordinator.data["usage"][0]["data"]
            daily_cost = sum(item.get("cost", 0) for item in hourly_data)
            
            # Calculate average rate if we have consumption data
            daily_consumption = sum(item.get("consumption", 0) for item in hourly_data)
            avg_rate = (daily_cost / daily_consumption) if daily_consumption > 0 else 0
            
            return {
                "hourly_breakdown": hourly_data,
                "last_update_date": self._last_processed_date,
                "daily_total_cost": round(daily_cost, 2),
                "average_rate_per_kwh": round(avg_rate, 4),
                "measurement_date": hourly_data[0]["date"][:10] if hourly_data and "date" in hourly_data[0] else None
            }
        except (KeyError, IndexError, TypeError, ZeroDivisionError):
            return {}
            
    async def async_added_to_hass(self):
        """Restore last known state when added to hass."""
        await super().async_added_to_hass()
        
        # Restore the last known state
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._cumulative_cost = float(last_state.state)
                if last_state.attributes:
                    self._last_processed_date = last_state.attributes.get("last_update_date")
            except (ValueError, TypeError):
                pass