# Mercury NZ Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

An unofficial Home Assistant integration for Mercury NZ electricity customers to monitor their power usage and costs.

## Features

- Real-time electricity usage monitoring
- Cost tracking in NZD
- Hourly usage data with historical access
- Automatic OAuth2 token refresh
- Configurable polling intervals

## Prerequisites

- Home Assistant 2023.1 or newer
- [HACS](https://hacs.xyz/) installed (recommended for easy installation and updates)
- Mercury NZ account with API access
- OAuth2 credentials (Client ID and refresh token)

## Installation

### Method 1: HACS (Recommended)

#### Add as Custom Repository

1. Open HACS in your Home Assistant instance
2. Click the three dots menu in the top right corner
3. Select **Custom repositories**
4. Add the repository:
   - **Repository**: `https://github.com/preetpatel/mercury-nz-homeassistant`
   - **Category**: `Integration`
5. Click **Add**
6. Close the custom repositories window
7. Click **+ Explore & Download Repositories**
8. Search for "Mercury NZ"
9. Click **Download**
10. Restart Home Assistant

### Method 2: Manual Installation

1. Download this repository
2. Copy the `custom_components/mercury_nz` folder to your Home Assistant's `custom_components` directory
3. Your Home Assistant configuration directory should look like:
   ```
   config/
   └── custom_components/
       └── mercury_nz/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── oauth.py
           └── sensor.py
   ```
4. Restart Home Assistant

## Configuration

### Step 1: Obtain Your Mercury NZ API Credentials

You'll need the following information from your Mercury NZ account:
- **Customer ID**: Your Mercury customer number
- **Account ID**: Your account identifier
- **Service ID**: Your electricity service identifier
- **API Subscription Key**: Azure API Management subscription key (Ocp-Apim-Subscription-Key)
- **Refresh Token**: Initial OAuth2 refresh token

### Step 2: Add Integration in Home Assistant

1. Navigate to **Settings** → **Devices & Services**
2. Click **Add Integration** (+)
3. Search for "Mercury NZ"
4. Enter your credentials:
   - Customer ID
   - Account ID
   - Service ID
   - API Subscription Key
   - Refresh Token
   
   Advanced (optional - have defaults):
   - Client ID (pre-filled with Mercury's default)
   - OAuth2 scope (pre-filled with required scopes)
   - Custom token URL (pre-filled with Mercury's endpoint)

### Step 3: Configure Options (Optional)

After adding the integration, you can configure:
- **Polling Interval**: How often to fetch data (default: 15 minutes)

## Sensors

The integration creates two daily sensors showing complete 24-hour data from 48 hours ago:

### Mercury Daily Energy
- **Entity ID**: `sensor.mercury_daily_energy`
- **Unit**: kWh
- **Device Class**: energy
- **State Class**: total_increasing
- **Description**: Daily energy consumption from 48 hours ago (complete 24-hour data)
- **Value**: Total kWh for the day (resets when new day's data arrives)
- **Attributes**: 
  - `measurement_date`: The actual date this data is from
  - `hourly_data`: Full 24-hour breakdown
  - `peak_hour`: Hour with highest consumption (0-23)
  - `peak_consumption`: Maximum hourly consumption
  - `average_hourly`: Average consumption per hour

### Mercury Daily Cost
- **Entity ID**: `sensor.mercury_daily_cost`
- **Unit**: NZD
- **Device Class**: monetary
- **State Class**: total
- **Description**: Daily energy cost from 48 hours ago
- **Value**: Total cost for the day
- **Attributes**: 
  - `measurement_date`: The actual date this data is from
  - `hourly_costs`: Breakdown by hour with cost and consumption
  - `average_rate_per_kwh`: Average rate for the day
  - `peak_rate_per_kwh`: Highest rate during the day
  - `lowest_rate_per_kwh`: Lowest rate during the day

**Important Notes**: 
- Mercury's API has a 48-hour delay (e.g., on August 9th, data from August 7th is available)
- Sensors show daily totals that reset when new data arrives
- Use Utility Meter helpers for cumulative tracking (see below)

## Energy Dashboard Setup

### Step 1: Create Utility Meter Helper

Since the sensors show daily totals, you need to create a Utility Meter helper for cumulative tracking:

1. Go to **Settings** → **Devices & Services** → **Helpers**
2. Click **+ Create Helper** → **Utility Meter**
3. Configure the helper:
   - **Name**: Mercury Energy Total (or similar)
   - **Input sensor**: `sensor.mercury_daily_energy`
   - **Meter reset cycle**: Choose based on your needs:
     - `no cycle` - Never resets (cumulative forever)
     - `daily` - Resets every day
     - `weekly` - Resets every week
     - `monthly` - Resets every month
     - `yearly` - Resets every year
   - **Meter reset offset**: 0
   - **Tariffs**: Leave empty unless you have different rate periods
4. Click **Submit**

### Step 2: Add to Energy Dashboard

1. Go to **Settings** → **Dashboards** → **Energy**
2. Click **Add Consumption** in the Grid section
3. Select your newly created **Utility Meter** helper (e.g., `sensor.mercury_energy_total`)
4. Choose how to track costs:
   - **Use entity with current price**: Enter a fixed price per kWh
   - **Use an entity tracking the total costs**: Create another Utility Meter for `sensor.mercury_daily_cost`
5. Click **Save**

### Understanding the Data Flow

```
Mercury API (48hr delay) → Daily Sensors → Utility Meter → Energy Dashboard
    Aug 7 data      →    Aug 9 update  →  Accumulates  →  Shows in stats
```

### Viewing Energy Data

The Energy Dashboard will show:
- **Daily consumption**: Each day's total when it arrives
- **Weekly/Monthly views**: Accumulated totals
- **Historical data**: Builds up over time
- **Cost tracking**: If configured with cost entity

**Note**: Data appears with a 48-hour delay but is correctly attributed to consumption periods.

## Example Automations

### Daily Usage Alert
```yaml
automation:
  - alias: "Daily Usage Alert"
    trigger:
      - platform: state
        entity_id: sensor.mercury_daily_energy
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state | float > 0 and trigger.to_state.state != trigger.from_state.state }}"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Energy data for {{ state_attr('sensor.mercury_daily_energy', 'measurement_date') }}:
            Usage: {{ states('sensor.mercury_daily_energy') }} kWh
            Cost: ${{ states('sensor.mercury_daily_cost') }}
            Peak hour: {{ state_attr('sensor.mercury_daily_energy', 'peak_hour') }}:00
            Peak usage: {{ state_attr('sensor.mercury_daily_energy', 'peak_consumption') }} kWh
```

### High Daily Usage Alert
```yaml
automation:
  - alias: "High Daily Usage Alert"
    trigger:
      - platform: state
        entity_id: sensor.mercury_daily_energy
    condition:
      - condition: template
        value_template: "{{ states('sensor.mercury_daily_energy') | float > 30 }}"
    action:
      - service: notify.mobile_app
        data:
          message: >
            ⚠️ High usage on {{ state_attr('sensor.mercury_daily_energy', 'measurement_date') }}!
            Total: {{ states('sensor.mercury_daily_energy') }} kWh
            Cost: ${{ states('sensor.mercury_daily_cost') }}
            Average rate: ${{ state_attr('sensor.mercury_daily_cost', 'average_rate_per_kwh') }}/kWh
```

## Dashboard Card Example

```yaml
type: vertical-stack
cards:
  - type: entity
    entity: sensor.mercury_daily_energy
    name: Daily Energy (48hr delay)
    icon: mdi:lightning-bolt
    
  - type: entity
    entity: sensor.mercury_daily_cost
    name: Daily Cost
    icon: mdi:currency-usd
    
  - type: attribute
    entity: sensor.mercury_daily_energy
    attribute: measurement_date
    name: Data Date
    icon: mdi:calendar
    
  - type: gauge
    entity: sensor.mercury_daily_energy
    name: Daily Usage
    unit: kWh
    min: 0
    max: 50
    severity:
      green: 0
      yellow: 20
      red: 35
    
  - type: custom:mini-graph-card
    entities:
      - entity: sensor.mercury_daily_energy
        name: Daily Energy
    hours_to_show: 168
    points_per_hour: 0.042
    show:
      labels: true
      points: true
```

### Utility Meter Card
```yaml
type: entities
entities:
  - entity: sensor.mercury_energy_total  # Your utility meter helper
    name: Total Energy This Month
  - type: divider
  - entity: sensor.mercury_daily_energy
    type: custom:multiple-entity-row
    name: Latest Daily Data
    secondary_info:
      attribute: measurement_date
    entities:
      - attribute: peak_hour
        name: Peak Hr
      - attribute: average_hourly
        name: Avg/Hr
```

## Troubleshooting

### Integration Not Showing Up
- Ensure the `mercury_nz` folder is in the correct location
- Check Home Assistant logs for errors: **Settings** → **System** → **Logs**
- Restart Home Assistant after installation

### Authentication Errors
- Verify your refresh token is valid
- Check that the Client ID matches your Mercury NZ API application
- The integration will automatically refresh expired access tokens

### No Data Appearing
- Wait for the first polling interval (default 15 minutes)
- Check sensor attributes for error messages
- Verify your Customer ID, Account ID, and Service ID are correct

### Rate Limiting
- Increase the polling interval if you encounter rate limits
- Default 15-minute interval should be safe for most users

## API Information

This integration uses Mercury NZ's self-service API:
- **Base URL**: `https://apis.mercury.co.nz/selfservice/v1`
- **Authentication**: OAuth2 with refresh token flow
- **API Management**: Requires Ocp-Apim-Subscription-Key header
- **Data**: Hourly electricity usage and cost information

## Disclaimer

This is an unofficial integration not affiliated with Mercury NZ. Use at your own risk. Always follow Mercury NZ's terms of service when accessing their API.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/preetpatel/mercury-nz-homeassistant/issues) page.