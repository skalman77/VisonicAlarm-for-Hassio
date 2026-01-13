"""The Visonic Alarm integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'visonicalarm'
PLATFORMS = [Platform.ALARM_CONTROL_PANEL, Platform.BINARY_SENSOR]

SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Visonic Alarm component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Visonic Alarm from a config entry."""
    from visonic import alarm as visonic_alarm

    # Skapa en klass-wrapper för att hantera alarm-instansen
    class VisonicHub:
        """Wrapper class for Visonic Alarm."""
        
        def __init__(self, alarm_instance, config_data):
            self.alarm = alarm_instance
            self.config = config_data
            self.last_update = None
            
        def update(self):
            """Update alarm data."""
            self.alarm.update()
            self.last_update = self.alarm.last_update if hasattr(self.alarm, 'last_update') else None

    # Skapa och anslut till alarm
    try:
        # Skapa alarm-instans i executor
        alarm_instance = await hass.async_add_executor_job(
            visonic_alarm.Setup,
            entry.data['host'],
            entry.data['app_id'],
            entry.data['user_email'],
            entry.data['user_password'],
            entry.data['panel_id'],
            entry.data.get('partition', -1)
        )
        
        # Skapa hub-wrapper
        hub = VisonicHub(alarm_instance, entry.data)
        
        # Initial update
        await hass.async_add_executor_job(hub.update)
        
    except Exception as err:
        _LOGGER.error('Failed to setup Visonic Alarm: %s', err)
        raise ConfigEntryNotReady(f'Could not connect to Visonic Alarm: {err}') from err

    # Spara data
    hass.data[DOMAIN][entry.entry_id] = {
        'hub': hub,
        'alarm': alarm_instance,
        'config': entry.data,
        'options': entry.options,
    }

    # Ladda plattformar
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Lyssna på options-uppdateringar
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
