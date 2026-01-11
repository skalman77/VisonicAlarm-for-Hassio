"""Interfaces with the Visonic Alarm control panel."""
import logging
from time import sleep

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelState,
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
import homeassistant.components.persistent_notification as pn
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_CODE_FORMAT,
    EVENT_STATE_CHANGED,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_USER_CODE,
    CONF_NO_PIN_REQUIRED,
    CONF_EVENT_HOUR_OFFSET,
)

_LOGGER = logging.getLogger(__name__)

ATTR_SYSTEM_SERIAL_NUMBER = 'serial_number'
ATTR_SYSTEM_MODEL = 'model'
ATTR_SYSTEM_READY = 'ready'
ATTR_SYSTEM_CONNECTED = 'connected'
ATTR_SYSTEM_SESSION_TOKEN = 'session_token'
ATTR_SYSTEM_LAST_UPDATE = 'last_update'
ATTR_CHANGED_BY = 'changed_by'
ATTR_CHANGED_TIMESTAMP = 'changed_timestamp'
ATTR_ALARMS = 'alarm'

SUPPORT_VISONIC = (
    AlarmControlPanelEntityFeature.ARM_HOME | AlarmControlPanelEntityFeature.ARM_AWAY
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Visonic Alarm from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data['coordinator']
    alarm = data['alarm']
    config = data['config']
    options = data['options']

    visonic_alarm = VisonicAlarm(coordinator, alarm, config, options, entry)
    async_add_entities([visonic_alarm])

    # Create event listener for arm state changes
    def arm_event_listener(event):
        entity_id = event.data.get('entity_id')
        old_state = event.data.get('old_state')
        new_state = event.data.get('new_state')

        if new_state is None or new_state.state in (STATE_UNKNOWN, ''):
            return None

        if (
            entity_id == visonic_alarm.entity_id
            and old_state is not None
            and old_state.state != new_state.state
        ):
            state = new_state.state
            if state in ['armed_home', 'armed_away', 'disarmed']:
                try:
                    last_event = alarm.get_last_event(
                        timestamp_hour_offset=visonic_alarm.event_hour_offset
                    )
                    visonic_alarm.update_last_event(
                        last_event['user'], last_event['timestamp']
                    )
                except Exception as err:
                    _LOGGER.error('Failed to get last event: %s', err)

    hass.bus.async_listen(EVENT_STATE_CHANGED, arm_event_listener)


class VisonicAlarm(CoordinatorEntity, AlarmControlPanelEntity):
    """Representation of a Visonic Alarm control panel."""

    _attr_supported_features = SUPPORT_VISONIC

    def __init__(self, coordinator, alarm, config, options, entry):
        """Initialize the Visonic Alarm panel."""
        super().__init__(coordinator)
        self._alarm = alarm
        self._config = config
        self._options = options
        self._entry = entry
        self._attr_alarm_state = None

        # Read config
        raw_code = config.get(CONF_USER_CODE)
        self._code = str(raw_code) if raw_code is not None else None

        # Check options first, then config
        self._no_pin_required = options.get(
            CONF_NO_PIN_REQUIRED,
            config.get(CONF_NO_PIN_REQUIRED, False)
        )
        
        self._event_hour_offset = options.get(
            CONF_EVENT_HOUR_OFFSET,
            config.get(CONF_EVENT_HOUR_OFFSET, 0)
        )

        self._changed_by = None
        self._changed_timestamp = None

        # Expose code format
        self._attr_code_format = None if self._no_pin_required else 'number'
        
        # Unique ID and device info
        self._attr_unique_id = f'{alarm.serial_number}_alarm'
        self._attr_device_info = {
            'identifiers': {(DOMAIN, alarm.serial_number)},
            'name': f'Visonic Alarm {alarm.serial_number}',
            'manufacturer': 'Visonic',
            'model': alarm.model,
        }

    @property
    def name(self):
        """Return the name of the device."""
        return 'Visonic Alarm'

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the alarm system."""
        return {
            ATTR_SYSTEM_SERIAL_NUMBER: self._alarm.serial_number,
            ATTR_SYSTEM_MODEL: self._alarm.model,
            ATTR_SYSTEM_READY: self._alarm.ready,
            ATTR_SYSTEM_CONNECTED: self._alarm.connected,
            ATTR_SYSTEM_SESSION_TOKEN: self._alarm.session_token,
            ATTR_CODE_FORMAT: self.code_format,
            ATTR_CHANGED_BY: self.changed_by,
            ATTR_CHANGED_TIMESTAMP: self._changed_timestamp,
            ATTR_ALARMS: self._alarm.alarm,
        }

    @property
    def icon(self):
        """Return icon."""
        if self._attr_alarm_state == AlarmControlPanelState.ARMED_AWAY:
            return 'mdi:shield-lock'
        elif self._attr_alarm_state == AlarmControlPanelState.ARMED_HOME:
            return 'mdi:shield-home'
        elif self._attr_alarm_state == AlarmControlPanelState.DISARMED:
            return 'mdi:shield-check'
        elif self._attr_alarm_state == AlarmControlPanelState.ARMING:
            return 'mdi:shield-outline'
        else:
            return 'hass:bell-ring'

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the alarm."""
        return self._attr_alarm_state

    @property
    def code_format(self):
        """Return the code format expected by the alarm."""
        return self._attr_code_format

    @property
    def code_arm_required(self):
        """Return if code is required for arming."""
        return not self._no_pin_required

    @property
    def code_disarm_required(self):
        """Return if code is required for disarming."""
        return not self._no_pin_required

    @property
    def changed_by(self):
        """Return the last change triggered by."""
        return self._changed_by

    @property
    def changed_timestamp(self):
        """Return the last change triggered by."""
        return self._changed_timestamp

    @property
    def event_hour_offset(self):
        """Return the hour offset to be used in the event log."""
        return self._event_hour_offset

    def update_last_event(self, user, timestamp):
        """Update with the user and timestamp of the last state change."""
        self._changed_by = user
        self._changed_timestamp = timestamp
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        status = self._alarm.state

        if status == 'AWAY':
            self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY
        elif status == 'HOME':
            self._attr_alarm_state = AlarmControlPanelState.ARMED_HOME
        elif status == 'DISARM':
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
        elif status == 'ARMING':
            self._attr_alarm_state = AlarmControlPanelState.ARMING
        elif status == 'ENTRYDELAY':
            self._attr_alarm_state = AlarmControlPanelState.PENDING
        elif status == 'ALARM':
            self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
        else:
            try:
                _LOGGER.warning('Unknown alarm state: %s. Trying to parse.', status)
                parsed_status = AlarmControlPanelState(status.lower())
                self._attr_alarm_state = parsed_status
            except ValueError:
                _LOGGER.error('Unable to parse alarm state: %s', status)
                pn.create(
                    self.hass,
                    f'Unknown alarm state: {status}',
                    title='Alarm State Error',
                )
                self._attr_alarm_state = None

        super()._handle_coordinator_update()

    def _validate_code(self, code, action_title: str, fail_message: str) -> bool:
        """Validate a provided code against configured code when PIN is required."""
        if self._no_pin_required:
            return True

        if self._code is None:
            pn.create(
                self.hass,
                'No user_code configured for this alarm integration.',
                title=action_title,
            )
            return False

        if code is None:
            pn.create(self.hass, fail_message, title=action_title)
            return False

        if str(code) != self._code:
            pn.create(self.hass, 'You entered the wrong code.', title=action_title)
            return False

        return True

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        if not self._validate_code(
            code=code,
            action_title='Disarm Failed',
            fail_message='A code is required to disarm, but no code was provided.',
        ):
            return

        await self.hass.async_add_executor_job(self._alarm.disarm)
        await self.hass.async_add_executor_job(sleep, 1)
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        if not self._validate_code(
            code=code,
            action_title='Arm Failed',
            fail_message='A code is required to arm, but no code was provided.',
        ):
            return

        if self._alarm.ready:
            await self.hass.async_add_executor_job(self._alarm.arm_home)
            await self.hass.async_add_executor_job(sleep, 1)
            await self.coordinator.async_request_refresh()
        else:
            pn.create(
                self.hass,
                'The alarm system is not in a ready state. '
                'Maybe there are doors or windows open?',
                title='Arm Failed',
            )

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        if not self._validate_code(
            code=code,
            action_title='Unable to Arm',
            fail_message='A code is required to arm, but no code was provided.',
        ):
            return

        if self._alarm.ready:
            await self.hass.async_add_executor_job(self._alarm.arm_away)
            await self.hass.async_add_executor_job(sleep, 1)
            await self.coordinator.async_request_refresh()
        else:
            pn.create(
                self.hass,
                'The alarm system is not in a ready state. '
                'Maybe there are doors or windows open?',
                title='Unable to Arm',
            )