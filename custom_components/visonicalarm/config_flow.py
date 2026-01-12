"""Config flow for Visonic Alarm integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PANEL_ID,
    CONF_USER_CODE,
    CONF_APP_ID,
    CONF_USER_EMAIL,
    CONF_USER_PASSWORD,
    CONF_PARTITION,
    CONF_NO_PIN_REQUIRED,
    CONF_EVENT_HOUR_OFFSET,
)

_LOGGER = logging.getLogger(__name__)


class VisonicAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Visonic Alarm."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                await self.async_set_unique_id(str(user_input[CONF_PANEL_ID]))
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f'Visonic Alarm {user_input[CONF_PANEL_ID]}',
                    data=user_input,
                )
            except Exception as err:
                _LOGGER.error('Failed to connect to Visonic Alarm: %s', err)
                errors['base'] = 'cannot_connect'

        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PANEL_ID): cv.positive_int,
            vol.Required(CONF_USER_CODE): cv.positive_int,
            vol.Required(CONF_APP_ID): str,
            vol.Required(CONF_USER_EMAIL): str,
            vol.Required(CONF_USER_PASSWORD): str,
            vol.Optional(CONF_PARTITION, default=-1): int,
            vol.Optional(CONF_NO_PIN_REQUIRED, default=False): bool,
            vol.Optional(CONF_EVENT_HOUR_OFFSET, default=0): int,
        })

        return self.async_show_form(
            step_id='user',
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return VisonicAlarmOptionsFlow(config_entry)


class VisonicAlarmOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Visonic Alarm."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title='', data=user_input)

        data_schema = vol.Schema({
            vol.Optional(
                CONF_NO_PIN_REQUIRED,
                default=self.config_entry.options.get(
                    CONF_NO_PIN_REQUIRED,
                    self.config_entry.data.get(CONF_NO_PIN_REQUIRED, False)
                ),
            ): bool,
            vol.Optional(
                CONF_EVENT_HOUR_OFFSET,
                default=self.config_entry.options.get(
                    CONF_EVENT_HOUR_OFFSET,
                    self.config_entry.data.get(CONF_EVENT_HOUR_OFFSET, 0)
                ),
            ): int,
        })

        return self.async_show_form(
            step_id='init',
            data_schema=data_schema,
        )
