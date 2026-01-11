# Visonic Alarm for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?style=for-the-badge)](https://www.buymeacoffee.com/4nd3rs)

Visonic/Bentel/Tyco Alarm System integration for Home Assistant with GUI configuration.

![Alarm Dialog](HomeAssistantArmDialog2.png)

## Overview

This integration allows you to control your Visonic alarm system directly from Home Assistant. It connects to the API server used by the Visonic-GO and BW apps.

### Features

- 🔐 **Alarm Control Panel** - Arm and disarm your system
- 🚪 **Door/Window Sensors** - Monitor all your contacts
- 🏠 **Home and Away Modes** - Support for different alarm modes
- 🔢 **PIN Code Support** - Optional PIN code for security
- ⚙️ **GUI Configuration** - Easy setup without YAML

### Compatibility

Tested with:
- Visonic PowerMaster 10 with PowerLink 3
- Visonic PowerMaster 30

Should work with most Visonic/Bentel/Tyco systems that use the Visonic-GO or BW app.

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click on **⋮** (three dots in the upper right)
4. Select **Custom repositories**
5. Add: `https://github.com/skalman77/VisonicAlarm-for-Hassio`
6. Select category: **Integration**
7. Click **Add**
8. Search for **Visonic Alarm**
9. Click **Download**
10. Restart Home Assistant

### Manual Installation

1. Download the latest version from [Releases](https://github.com/skalman77/VisonicAlarm-for-Hassio/releases)
2. Copy the `custom_components/visonicalarm` folder to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

**NOTE!** This integration is configured via GUI, not YAML.

### Step 1: Gather Information

You need the following credentials (same as you use in the Visonic-GO/BW app):

- **Host**: e.g. `company.tycomonitor.com`
- **Panel ID**: Found in your app
- **User Code**: Your Master User PIN code
- **App ID**: Generate a UUID at [uuidgenerator.net](https://www.uuidgenerator.net/)
- **Email**: Your Visonic account email
- **Password**: Your Visonic account password
- **Partition**: `-1` (default for most systems)

### Step 2: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Visonic Alarm**
4. Fill in the form with the information above
5. Click **Submit**

### Step 3: Configure Settings (Optional)

After installation you can change certain settings:

1. Go to **Devices & Services**
2. Find **Visonic Alarm**
3. Click **Configure**
4. Modify:
   - **No PIN Required**: Skip PIN code when arming/disarming
   - **Event Hour Offset**: Adjust timezone for event log

## Usage

### Entities

After configuration, the following entities are created:

#### Alarm Control Panel
- `alarm_control_panel.visonic_alarm`

**States:**
- `disarmed` - Disarmed
- `armed_home` - Armed Home
- `armed_away` - Armed Away
- `arming` - Arming
- `pending` - Pending (entry delay)
- `triggered` - Triggered

#### Binary Sensors (Contacts)
- `binary_sensor.visonic_alarm_contact_1`
- `binary_sensor.visonic_alarm_contact_2`
- etc.

**States:**
- `on` - Open
- `off` - Closed

### Automations

```yaml
automation:
  # Arm when everyone leaves
  - alias: "Auto arm when everyone leaves"
    trigger:
      - platform: state
        entity_id: group.all_persons
        to: 'not_home'
        for: '00:05:00'
    action:
      - service: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.visonic_alarm
        data:
          code: '1234'

  # Disarm when someone arrives
  - alias: "Disarm when someone arrives"
    trigger:
      - platform: state
        entity_id: group.all_persons
        to: 'home'
    condition:
      - condition: state
        entity_id: alarm_control_panel.visonic_alarm
        state: 'armed_away'
    action:
      - service: alarm_control_panel.alarm_disarm
        target:
          entity_id: alarm_control_panel.visonic_alarm
        data:
          code: '1234'

  # Notify if door opens when armed
  - alias: "Notify if door opens when armed"
    trigger:
      - platform: state
        entity_id: binary_sensor.visonic_alarm_contact_1
        to: 'on'
    condition:
      - condition: state
        entity_id: alarm_control_panel.visonic_alarm
        state: 'armed_away'
    action:
      - service: notify.mobile_app
        data:
          message: "Warning! Door opened while system was armed!"
```

### Lovelace Card

```yaml
type: alarm-panel
entity: alarm_control_panel.visonic_alarm
states:
  - arm_away
  - arm_home
```

## Troubleshooting

### Issue: Integration not showing in list

**Solution:**
- Verify files are in the correct directory: `config/custom_components/visonicalarm/`
- Restart Home Assistant
- Check logs for error messages

### Issue: Cannot connect to alarm system

**Solution:**
- Verify credentials are correct (test in Visonic app first)
- Ensure user is **Master User** in the system
- Double-check hostname (same as in app)
- Verify internet connection

### Issue: Sensors not appearing

**Solution:**
- Verify zones are enabled in alarm system
- Wait 10-30 seconds after configuration
- Restart Home Assistant
- Check logs for error messages

### Issue: PIN code not accepted

**Solution:**
- Verify `user_code` matches your Master User PIN
- Check for typos in configuration
- If "No PIN Required" is enabled, no code is needed

## Migrating from YAML

If you previously used YAML configuration:

1. **Backup** - Backup your `configuration.yaml`

2. **Remove YAML configuration:**
```yaml
# REMOVE THIS FROM configuration.yaml:
visonicalarm:
  host: YOURALARMCOMPANY.tycomonitor.com
  panel_id: 123456
  # etc...
```

3. **Restart** Home Assistant

4. **Configure via GUI** following the instructions above

**NOTE!** Your entities will keep the same entity_id, so your automations should continue working.

## Known Limitations

- Only partition `-1` (default) supported per integration instance
- Alarm system is polled every 10 seconds (same as the app)
- Requires Master User privileges

## Support

If you encounter issues:

1. Check [GitHub Issues](https://github.com/skalman77/VisonicAlarm-for-Hassio/issues)
2. Check Home Assistant logs: **Settings** → **System** → **Logs**
3. Create a new issue with:
   - Home Assistant version
   - Error message from logs
   - Steps to reproduce the problem

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)

## Credits

- Original integration by [@And3rsL](https://github.com/And3rsL)
- Python library [VisonicAlarm2](https://github.com/And3rsL/VisonicAlarm2)

## Disclaimer

**IMPORTANT:** This integration is NOT officially supported by Visonic, Bentel or Tyco. It uses their unpublished REST API. I accept no liability for any loss or damage that may result from using this integration.

Use at your own risk.

---

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/default-black.png)](https://www.buymeacoffee.com/4nd3rs)

If you like this integration, consider supporting the original developer!