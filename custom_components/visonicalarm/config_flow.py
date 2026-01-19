"""Config flow for Visonic Alarm integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

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


def _normalize_host(host: str) -> str:
    host = host.strip()
    host = host.replace("https://", "").replace("http://", "").rstrip("/")
    return host


def _digits_only(value: str) -> str:
    value = value.strip()
    if not value.isdigit():
        raise vol.Invalid("must be digits only")
    return value


class VisonicAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Visonic Alarm."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Normalize values to match how YAML commonly behaved
                user_input[CONF_HOST] = _normalize_host(user_input[CONF_HOST])
                user_input[CONF_PANEL_ID] = _digits_only(user_input[CONF_PANEL_ID])
                user_input[CONF_USER_CODE] = _digits_only(user_input[CONF_USER_CODE])

                await self.async_set_unique_id(str(user_input[CONF_PANEL_ID]))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Visonic Alarm {user_input[CONF_PANEL_ID]}",
                    data=user_input,
                )
            except vol.Invalid:
                # Specific field errors: show a general error for now
                errors["base"] = "invalid_input"
            except Exception as err:
                _LOGGER.error("Failed to create Visonic Alarm entry: %s", err)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                # Store these as strings (API can be picky about types)
                vol.Required(CONF_PANEL_ID): str,
                vol.Required(CONF_USER_CODE): str,
                vol.Required(CONF_APP_ID): str,
                vol.Required(CONF_USER_EMAIL): str,
                vol.Required(CONF_USER_PASSWORD): str,
                vol.Optional(CONF_PARTITION, default="-1"): str,
                vol.Optional(CONF_NO_PIN_REQUIRED, default=False): bool,
                vol.Optional(CONF_EVENT_HOUR_OFFSET, default=0): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return VisonicAlarmOptionsFlow()


class VisonicAlarmOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Visonic Alarm."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Använd self.config_entry direkt från bas-klassen
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NO_PIN_REQUIRED,
                    default=self.config_entry.options.get(
                        CONF_NO_PIN_REQUIRED,
                        self.config_entry.data.get(CONF_NO_PIN_REQUIRED, False),
                    ),
                ): bool,
                vol.Optional(
                    CONF_EVENT_HOUR_OFFSET,
                    default=self.config_entry.options.get(
                        CONF_EVENT_HOUR_OFFSET,
                        self.config_entry.data.get(CONF_EVENT_HOUR_OFFSET, 0),
                    ),
                ): int,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
