from __future__ import annotations
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import MercuryCoordinator

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: MercuryCoordinator = hass.data[entry.domain][entry.entry_id]
    async_add_entities([
        MercuryDailyEnergySensor(coordinator, entry),
        MercuryDailyCostSensor(coordinator, entry),
    ])

class MercuryDailyEnergySensor(CoordinatorEntity, SensorEntity):
    """Daily energy consumption sensor showing data from 48 hours ago."""
    
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "kWh"
    _attr_name = "Mercury Daily Energy"
    _attr_icon = "mdi:lightning-bolt"
    
    def __init__(self, coordinator: MercuryCoordinator, entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_energy"
        
    @property
    def native_value(self):
        """Return the daily total energy consumption from 48 hours ago."""
        if not self.coordinator.data:
            return 0
            
        try:
            hourly_data = self.coordinator.data["usage"][0]["data"]
            if hourly_data:
                # Sum all 24 hours of consumption
                daily_total = sum(item.get("consumption", 0) for item in hourly_data)
                return round(daily_total, 3) if daily_total > 0 else 0
        except (KeyError, IndexError, TypeError):
            pass
            
        return 0
    
    @property
    def extra_state_attributes(self):
        """Include the full 24-hour breakdown and metadata."""
        if not self.coordinator.data:
            return {}
            
        try:
            hourly_data = self.coordinator.data["usage"][0]["data"]
            if not hourly_data:
                return {}
                
            # Extract the date from the first hourly entry
            measurement_date = hourly_data[0].get("date", "")[:10] if hourly_data else None
            
            # Calculate hourly statistics
            hourly_values = [item.get("consumption", 0) for item in hourly_data]
            peak_hour = max(range(len(hourly_values)), key=lambda i: hourly_values[i]) if hourly_values else None
            
            return {
                "measurement_date": measurement_date,
                "hourly_data": hourly_data,
                "peak_hour": peak_hour,
                "peak_consumption": round(max(hourly_values), 3) if hourly_values else 0,
                "average_hourly": round(sum(hourly_values) / 24, 3) if hourly_values else 0,
                "data_delay_hours": 48,
            }
        except (KeyError, IndexError, TypeError, ValueError):
            return {}

class MercuryDailyCostSensor(CoordinatorEntity, SensorEntity):
    """Daily energy cost sensor showing data from 48 hours ago."""
    
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "NZD"
    _attr_name = "Mercury Daily Cost"
    _attr_icon = "mdi:currency-usd"
    
    def __init__(self, coordinator: MercuryCoordinator, entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_daily_cost"
        
    @property
    def native_value(self):
        """Return the daily total cost from 48 hours ago."""
        if not self.coordinator.data:
            return 0
            
        try:
            hourly_data = self.coordinator.data["usage"][0]["data"]
            if hourly_data:
                # Sum all 24 hours of cost
                daily_cost = sum(item.get("cost", 0) for item in hourly_data)
                return round(daily_cost, 2) if daily_cost > 0 else 0
        except (KeyError, IndexError, TypeError):
            pass
            
        return 0
    
    @property
    def extra_state_attributes(self):
        """Include cost breakdown and rate information."""
        if not self.coordinator.data:
            return {}
            
        try:
            hourly_data = self.coordinator.data["usage"][0]["data"]
            if not hourly_data:
                return {}
                
            # Extract the date
            measurement_date = hourly_data[0].get("date", "")[:10] if hourly_data else None
            
            # Calculate totals for rate calculation
            daily_cost = sum(item.get("cost", 0) for item in hourly_data)
            daily_consumption = sum(item.get("consumption", 0) for item in hourly_data)
            
            # Calculate average and peak rates
            hourly_rates = []
            for item in hourly_data:
                consumption = item.get("consumption", 0)
                cost = item.get("cost", 0)
                if consumption > 0:
                    hourly_rates.append(cost / consumption)
            
            avg_rate = (daily_cost / daily_consumption) if daily_consumption > 0 else 0
            peak_rate = max(hourly_rates) if hourly_rates else 0
            min_rate = min(hourly_rates) if hourly_rates else 0
            
            return {
                "measurement_date": measurement_date,
                "hourly_costs": [{
                    "hour": i,
                    "cost": round(item.get("cost", 0), 2),
                    "consumption": round(item.get("consumption", 0), 3)
                } for i, item in enumerate(hourly_data)],
                "average_rate_per_kwh": round(avg_rate, 4),
                "peak_rate_per_kwh": round(peak_rate, 4),
                "lowest_rate_per_kwh": round(min_rate, 4),
                "total_consumption_kwh": round(daily_consumption, 3),
                "data_delay_hours": 48,
            }
        except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError):
            return {}