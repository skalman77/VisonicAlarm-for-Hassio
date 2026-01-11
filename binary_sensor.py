"""Support for Visonic Alarm contact sensors."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Visonic contact sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data['coordinator']
    alarm = data['alarm']

    entities = []
    for contact in alarm.contacts:
        entities.append(VisonicContactSensor(coordinator, alarm, contact))

    async_add_entities(entities)


class VisonicContactSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Visonic contact sensor."""

    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(self, coordinator, alarm, contact):
        """Initialize the contact sensor."""
        super().__init__(coordinator)
        self._alarm = alarm
        self._contact = contact
        self._contact_id = contact['id']
        
        # Unique ID and device info
        self._attr_unique_id = f'{alarm.serial_number}_contact_{self._contact_id}'
        self._attr_device_info = {
            'identifiers': {(DOMAIN, alarm.serial_number)},
            'name': f'Visonic Alarm {alarm.serial_number}',
            'manufacturer': 'Visonic',
            'model': alarm.model,
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Visonic Alarm Contact {self._contact_id}"

    @property
    def is_on(self):
        """Return True if the contact is open."""
        for contact in self._alarm.contacts:
            if contact['id'] == self._contact_id:
                return contact['state'] == 'Open'
        return False

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        for contact in self._alarm.contacts:
            if contact['id'] == self._contact_id:
                return {
                    'zone_name': contact.get('name', f'Zone {self._contact_id}'),
                    'zone_type': contact.get('type', 'Unknown'),
                    'partition': contact.get('partition', -1),
                }
        return {}