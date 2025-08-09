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
- **Client ID**: OAuth2 client identifier
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
   - Client ID
   - API Subscription Key
   - Refresh Token
   - (Optional) Custom token URL
   - (Optional) OAuth2 scope

### Step 3: Configure Options (Optional)

After adding the integration, you can configure:
- **Polling Interval**: How often to fetch data (default: 15 minutes)
- **Timezone**: Your local timezone for accurate daily boundaries

## Sensors

The integration creates two sensors:

### Mercury Usage Total kWh
- **Entity ID**: `sensor.mercury_usage_total_kwh`
- **Unit**: kWh
- **Description**: Total electricity consumption for the current period
- **Attributes**: Hourly breakdown of usage

### Mercury Usage Total Cost
- **Entity ID**: `sensor.mercury_usage_total_cost`
- **Unit**: NZD
- **Description**: Total cost for the current period
- **Attributes**: Hourly breakdown of costs

## Example Automations

### High Usage Alert
```yaml
automation:
  - alias: "High Power Usage Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mercury_usage_total_kwh
        above: 50
    action:
      - service: notify.mobile_app
        data:
          message: "High power usage detected: {{ states('sensor.mercury_usage_total_kwh') }} kWh"
```

### Daily Usage Report
```yaml
automation:
  - alias: "Daily Usage Report"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Today's usage: {{ states('sensor.mercury_usage_total_kwh') }} kWh
            Cost: ${{ states('sensor.mercury_usage_total_cost') }}
```

## Dashboard Card Example

```yaml
type: vertical-stack
cards:
  - type: sensor
    entity: sensor.mercury_usage_total_kwh
    graph: line
    name: Electricity Usage
    
  - type: sensor
    entity: sensor.mercury_usage_total_cost
    graph: line
    name: Electricity Cost
    
  - type: statistics-graph
    entities:
      - sensor.mercury_usage_total_kwh
    stat_types:
      - mean
      - max
    period:
      calendar:
        period: week
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

## Development

### File Structure
- `__init__.py`: Integration setup and platform loading
- `config_flow.py`: Configuration UI flow
- `const.py`: Constants and API endpoints
- `coordinator.py`: Data update coordinator and API client
- `oauth.py`: OAuth2 token management
- `sensor.py`: Sensor entity definitions
- `manifest.json`: Integration metadata

### Testing Locally

1. Set up a Home Assistant development environment
2. Place the integration in your dev environment's `custom_components` folder
3. Add to your `configuration.yaml` for debugging:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.mercury_nz: debug
   ```

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request

## Disclaimer

This is an unofficial integration not affiliated with Mercury NZ. Use at your own risk. Always follow Mercury NZ's terms of service when accessing their API.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/preetpatel/mercury-nz-homeassistant/issues) page.