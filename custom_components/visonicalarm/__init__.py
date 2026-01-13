"""The Visonic Alarm integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.util import Throttle
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'visonicalarm'
PLATFORMS = [Platform.ALARM_CONTROL_PANEL, Platform.BINARY_SENSOR]

SCAN_INTERVAL = timedelta(seconds=10)

# Configuration keys
CONF_HOST = 'host'
CONF_PANEL_ID = 'panel_id'
CONF_USER_CODE = 'user_code'
CONF_APP_ID = 'app_id'
CONF_USER_EMAIL = 'user_email'
CONF_USER_PASSWORD = 'user_password'
CONF_PARTITION = 'partition'
CONF_NO_PIN_REQUIRED = 'no_pin_required'
CONF_EVENT_HOUR_OFFSET = 'event_hour_offset'


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Visonic Alarm component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Visonic Alarm from a config entry."""
    from visonic import alarm as visonic_alarm

    # Create hub wrapper - samma struktur som YAML-versionen
    class Hub:
        """Hub wrapper for Visonic Alarm."""
        
        def __init__(self):
            self.alarm = None
            self.config = entry.data
            self.last_update = None

        @Throttle(SCAN_INTERVAL)
        def update(self):
            """Update alarm data."""
            if self.alarm:
                self.alarm.update()
                self.last_update = self.alarm.last_update if hasattr(self.alarm, 'last_update') else None

    # Create hub instance
    hub = Hub()

    # Setup alarm - DET HÄR ÄR RÄTT ENLIGT ORIGINAL-KODEN
    try:
        # Skapa alarm-instansen i executor
        def setup_alarm():
            return visonic_alarm.Setup(
                entry.data[CONF_HOST],
                entry.data[CONF_APP_ID],
                entry.data[CONF_USER_EMAIL],
                entry.data[CONF_USER_PASSWORD],
                entry.data[CONF_PANEL_ID],
                entry.data.get(CONF_PARTITION, -1)
            )
        
        hub.alarm = await hass.async_add_executor_job(setup_alarm)
        
        # Initial update
        await hass.async_add_executor_job(hub.update)
        
    except Exception as err:
        _LOGGER.error('Failed to setup Visonic Alarm: %s', err)
        raise ConfigEntryNotReady(f'Could not connect to Visonic Alarm: {err}') from err

    # Spara hub
    hass.data[DOMAIN][entry.entry_id] = hub

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
