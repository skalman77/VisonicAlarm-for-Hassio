# Visonic Alarm Integration

Visonic/Bentel/Tyco Alarm System integration for Home Assistant with GUI configuration.

## ✨ Features

- 🔐 Alarm control panel for arming/disarming the system
- 🚪 Sensors for all door and window contacts
- 🏠 Support for both Home and Away modes
- 🔢 Optional PIN code for arming/disarming
- ⚙️ GUI configuration (no YAML files needed)

## 📋 Requirements

- Visonic/Bentel/Tyco alarm system with PowerLink module
- Visonic-GO or BW app with working account
- Master User privileges in the system

## 🚀 Installation

### Step 1: Install via HACS
1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click **⋮** (three dots) → **Custom repositories**
4. Add: `https://github.com/skalman77/VisonicAlarm-for-Hassio`
5. Category: **Integration**
6. Click **Add**
7. Search for **Visonic Alarm** and click **Download**
8. Restart Home Assistant

### Step 2: Configure the integration
1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Visonic Alarm**
4. Fill in the form:

| Field | Description | Example |
|------|-------------|---------|
| **Host** | Your alarm server address | `company.tycomonitor.com` |
| **Panel ID** | Panel ID from your app | `123456` |
| **User Code** | Your PIN code for the alarm | `1234` |
| **App ID** | UUID (generate at uuidgenerator.net) | `00000000-0000-0000-0000-000000000000` |
| **Email** | Your Visonic account email | `example@email.com` |
| **Password** | Your Visonic account password | `yourpassword` |
| **Partition** | Alarm zone (-1 for default) | `-1` |
| **No PIN Required** | Skip PIN when arming | `false` |
| **Event Hour Offset** | Timezone adjustment | `0` |

5. Click **Submit**

## ⚙️ Settings

After installation you can change certain settings:
1. Go to **Devices & Services**
2. Find **Visonic Alarm**
3. Click **Configure**
4. Modify **No PIN Required** or **Event Hour Offset**

## 📱 Created Entities

### Alarm Control Panel
- `alarm_control_panel.visonic_alarm`
  - States: `disarmed`, `armed_home`, `armed_away`, `arming`, `pending`, `triggered`

### Binary Sensors (Contacts)
- `binary_sensor.visonic_alarm_contact_1`
- `binary_sensor.visonic_alarm_contact_2`
- `binary_sensor.visonic_alarm_contact_X`
  - States: `on` (open), `off` (closed)

## 🎯 Usage

### In Home Assistant UI
1. Go to **Overview**
2. Find your **Visonic Alarm** card
3. Click to arm/disarm
4. Enter PIN code if enabled

### In Automations
```yaml
automation:
  - alias: "Arm when everyone leaves"
    trigger:
      - platform: state
        entity_id: group.all_persons
        to: 'not_home'
    action:
      - service: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.visonic_alarm
        data:
          code: '1234'
```

### In Scripts
```yaml
script:
  arm_alarm_home:
    sequence:
      - service: alarm_control_panel.alarm_arm_home
        target:
          entity_id: alarm_control_panel.visonic_alarm
        data:
          code: '1234'
```

## 🔧 Troubleshooting

### Integration not appearing
- Check that you restarted Home Assistant after installation
- Check logs: **Settings** → **System** → **Logs**

### Cannot connect
- Verify credentials are correct (test in Visonic app first)
- Check that you have Master User privileges
- Verify hostname is correct (same as in app)

### Sensors not appearing
- Check that your zones are enabled in the alarm system
- Wait 10-30 seconds after configuration
- Restart Home Assistant

### PIN code not working
- Verify `user_code` matches your Master User PIN
- Double-check you entered the correct code in configuration

## 📝 Migrating from YAML

If you previously used YAML configuration:

1. **Remove** this configuration from `configuration.yaml`:
```yaml
visonicalarm:
  host: ...
  panel_id: ...
  # etc.
```

2. Restart Home Assistant

3. Follow the installation instructions above to configure via GUI

## 🆘 Support

If you encounter problems:
1. Check [GitHub Issues](https://github.com/skalman77/VisonicAlarm-for-Hassio/issues)
2. Create a new issue if the problem isn't listed
3. Include Home Assistant logs and your configuration (hide sensitive info)

## 📜 License

MIT License - See [LICENSE](LICENSE) for details

## ☕ Support the Developer

If you like this integration, consider supporting the original developer:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/default-black.png)](https://www.buymeacoffee.com/4nd3rs)

---

**NOTE!** This integration is not officially supported by Visonic/Bentel/Tyco. Use at your own risk.