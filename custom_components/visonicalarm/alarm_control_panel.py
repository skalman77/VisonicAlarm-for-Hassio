"""Alarm control panel for Visonic Alarm."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelState,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

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

    # OBS: Ingen DISARM-flagga här (finns inte i alla HA-versioner).
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

    async def _call_alarm(self, method_name: str) -> None:
        """Call a blocking alarm method safely via executor and refresh."""
        method = getattr(self._alarm, method_name, None)
        if not callable(method):
            raise ValueError(f"Alarm method not supported by library: {method_name}")

        await self.hass.async_add_executor_job(method)
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._call_alarm("disarm")

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self._call_alarm("arm_home")

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self._call_alarm("arm_away")

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command (fallback to home if not supported)."""
        if callable(getattr(self._alarm, "arm_night", None)):
            await self._call_alarm("arm_night")
        else:
            _LOGGER.warning("arm_night not supported; falling back to arm_home")
            await self._call_alarm("arm_home")
