"""The Visonic Alarm integration."""
import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'visonicalarm'
PLATFORMS = [Platform.ALARM_CONTROL_PANEL, Platform.BINARY_SENSOR]

SCAN_INTERVAL = timedelta(seconds=10)

# Configuration keys - samma som den ursprungliga
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
    
    # Skapa hub-instans EXAKT som YAML-versionen
    class Hub:
        """Hub class - samma som YAML-versionen."""
        
        def __init__(self, config_data):
            self.alarm = None
            self.config = config_data
            self.last_update = None

        @Throttle(SCAN_INTERVAL)
        def update(self):
            """Update alarm data."""
            if self.alarm:
                self.alarm.update()
                self.last_update = getattr(self.alarm, 'last_update', None)

    hub = Hub(entry.data)

    # Setup alarm - EXAKT som YAML gör det (använder visonic-biblioteket)
    def setup_alarm():
        """Setup the alarm in a thread."""
        from visonic import alarm
        # Enligt YAML-koden skapas det så här
        return alarm.Setup(
            hub.config[CONF_HOST],
            hub.config[CONF_APP_ID],
            hub.config[CONF_USER_EMAIL],
            hub.config[CONF_USER_PASSWORD],
            hub.config[CONF_PANEL_ID],
            hub.config.get(CONF_PARTITION, -1)
        )

    try:
        hub.alarm = await hass.async_add_executor_job(setup_alarm)
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
