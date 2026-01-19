"""Alarm control panel for Visonic Alarm."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelState,
    AlarmControlPanelEntityFeature,
)
import homeassistant.components.persistent_notification as pn
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_USER_CODE, CONF_NO_PIN_REQUIRED

_LOGGER = logging.getLogger(__name__)


def _map_state(raw: Any) -> AlarmControlPanelState:
    """Map library state strings to HA states."""
    if raw is None:
        return AlarmControlPanelState.UNKNOWN

    s = str(raw).strip().upper()

    if s in ("DISARM", "DISARMED", "OFF"):
        return AlarmControlPanelState.DISARMED
    if s in ("HOME", "ARM_HOME", "STAY"):
        return AlarmControlPanelState.ARMED_HOME
    if s in ("AWAY", "ARM_AWAY"):
        return AlarmControlPanelState.ARMED_AWAY
    if s in ("NIGHT", "ARM_NIGHT"):
        return AlarmControlPanelState.ARMED_NIGHT

    if s in ("ARMING",):
        return AlarmControlPanelState.ARMING
    if s in ("PENDING", "ENTRY_DELAY", "EXIT_DELAY"):
        return AlarmControlPanelState.PENDING
    if s in ("TRIGGERED", "ALARM", "SIREN"):
        return AlarmControlPanelState.TRIGGERED

    return AlarmControlPanelState.UNKNOWN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up alarm control panel."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    alarm = data["alarm"]

    async_add_entities([VisonicAlarmControlPanel(coordinator, alarm, entry)], True)


class VisonicAlarmControlPanel(CoordinatorEntity, AlarmControlPanelEntity):
    """Representation of the Visonic alarm panel."""

    _attr_has_entity_name = True
    _attr_name = "Alarm"

    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(self, coordinator, alarm, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._alarm = alarm
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_alarm_panel"
        
        # Läs konfiguration och options
        self._user_code = str(entry.data.get(CONF_USER_CODE, ""))
        
        # Kolla options först, sedan data
        self._no_pin_required = entry.options.get(
            CONF_NO_PIN_REQUIRED,
            entry.data.get(CONF_NO_PIN_REQUIRED, False)
        )
        
        # Sätt code format baserat på no_pin_required
        self._attr_code_format = None if self._no_pin_required else "number"

    @property
    def code_format(self):
        """Return the code format."""
        return self._attr_code_format

    @property
    def code_arm_required(self) -> bool:
        """Return if code is required for arming."""
        return not self._no_pin_required

    @property
    def code_disarm_required(self) -> bool:
        """Return if code is required for disarming."""
        return not self._no_pin_required

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        """Return the state of the alarm."""
        raw_state = None
        if self.coordinator.data:
            raw_state = self.coordinator.data.get("state")
            if raw_state is None:
                raw_state = self.coordinator.data.get("status")
                if isinstance(raw_state, dict) and "state" in raw_state:
                    raw_state = raw_state.get("state")

        return _map_state(raw_state)

    def _validate_code(self, code: str | None, action: str) -> bool:
        """Validate the provided code."""
        # Om PIN inte krävs, godkänn alltid
        if self._no_pin_required:
            return True
        
        # Om PIN krävs men ingen kod angavs
        if code is None:
            pn.create(
                self.hass,
                f"A code is required to {action}, but no code was provided.",
                title=f"{action.capitalize()} Failed",
            )
            return False
        
        # Om ingen user_code är konfigurerad
        if not self._user_code:
            pn.create(
                self.hass,
                "No user_code configured for this alarm integration.",
                title=f"{action.capitalize()} Failed",
            )
            return False
        
        # Validera koden
        if str(code) != self._user_code:
            pn.create(
                self.hass,
                "You entered the wrong code.",
                title=f"{action.capitalize()} Failed",
            )
            return False
        
        return True

    async def _call_alarm(self, method_name: str, code: str | None, action: str) -> None:
        """Call a blocking alarm method safely via executor and refresh."""
        # Validera PIN-kod först
        if not self._validate_code(code, action):
            return
        
        method = getattr(self._alarm, method_name, None)
        if not callable(method):
            raise ValueError(f"Alarm method not supported by library: {method_name}")

        await self.hass.async_add_executor_job(method)
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._call_alarm("disarm", code, "disarm")

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self._call_alarm("arm_home", code, "arm")

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self._call_alarm("arm_away", code, "arm")

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command (fallback to home if not supported)."""
        # Validera PIN-kod först
        if not self._validate_code(code, "arm"):
            return
        
        if callable(getattr(self._alarm, "arm_night", None)):
            method = getattr(self._alarm, "arm_night")
            await self.hass.async_add_executor_job(method)
        else:
            _LOGGER.warning("arm_night not supported; falling back to arm_home")
            method = getattr(self._alarm, "arm_home")
            await self.hass.async_add_executor_job(method)
        
        await self.coordinator.async_request_refresh()
