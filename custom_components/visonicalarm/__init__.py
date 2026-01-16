"""The Visonic Alarm integration."""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any, Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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

PLATFORMS = [Platform.ALARM_CONTROL_PANEL, Platform.BINARY_SENSOR]
SCAN_INTERVAL = timedelta(seconds=10)

_DEVICES_REFRESH_SECONDS = 300  # var 5:e minut
_last_devices_refresh = 0.0


def _normalize_host(host: str) -> str:
    host = (host or "").strip()
    host = host.replace("https://", "").replace("http://", "").rstrip("/")
    return host


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _extract_devices(alarm: Any) -> list[Any]:
    """
    Best-effort extraction of devices/zones from different library versions.
    We try several common attributes & methods.
    """
    # 1) Common attribute names seen across versions/integrations
    for attr in ("contacts", "devices", "zones", "sensors"):
        v = getattr(alarm, attr, None)
        lst = _as_list(v)
        if lst:
            return lst

    # 2) Common method names
    for meth in ("get_devices", "get_zones", "get_contacts", "devices_list", "zones_list"):
        fn = getattr(alarm, meth, None)
        if callable(fn):
            try:
                v = fn()
                lst = _as_list(v)
                if lst:
                    return lst
            except Exception:
                _LOGGER.debug("Device extraction via %s() failed (ignored)", meth, exc_info=True)

    # 3) Some libs tuck devices inside status objects/dicts
    status = getattr(alarm, "status", None)
    if isinstance(status, dict):
        for k in ("devices", "zones", "contacts"):
            if k in status and isinstance(status[k], list) and status[k]:
                return status[k]

    return []


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (YAML not used)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Visonic Alarm from a config entry."""
    from visonic import alarm as visonic_alarm

    host = _normalize_host(str(entry.data.get(CONF_HOST, "")))
    app_id = str(entry.data.get(CONF_APP_ID, "")).strip()
    user_email = str(entry.data.get(CONF_USER_EMAIL, "")).strip()
    user_password = str(entry.data.get(CONF_USER_PASSWORD, ""))

    # Keep as strings (match original library usage)
    user_code = str(entry.data.get(CONF_USER_CODE, "")).strip()
    panel_id = str(entry.data.get(CONF_PANEL_ID, "")).strip()
    partition = str(entry.data.get(CONF_PARTITION, "-1")).strip()

    missing = []
    if not host:
        missing.append(CONF_HOST)
    if not app_id:
        missing.append(CONF_APP_ID)
    if not user_email:
        missing.append(CONF_USER_EMAIL)
    if not user_password:
        missing.append(CONF_USER_PASSWORD)
    if not user_code:
        missing.append(CONF_USER_CODE)
    if not panel_id:
        missing.append(CONF_PANEL_ID)

    if missing:
        raise ConfigEntryNotReady(f"Missing required config values: {', '.join(missing)}")

    no_pin_required = entry.options.get(
        CONF_NO_PIN_REQUIRED, entry.data.get(CONF_NO_PIN_REQUIRED, False)
    )
    event_hour_offset = entry.options.get(
        CONF_EVENT_HOUR_OFFSET, entry.data.get(CONF_EVENT_HOUR_OFFSET, 0)
    )

    def _create_and_connect():
        alarm = visonic_alarm.System(
            host,
            app_id,
            user_code,
            user_email,
            user_password,
            panel_id,
            partition,
        )

        alarm.connect()

        # Populate device list early
        try:
            alarm.update_devices()
        except Exception as dev_err:
            _LOGGER.warning("Connected, but initial update_devices() failed: %s", dev_err)

        return alarm

    try:
        alarm = await hass.async_add_executor_job(_create_and_connect)
        _LOGGER.info("Visonic Alarm connected successfully to %s", host)
    except Exception as err:
        _LOGGER.error("Could not connect/login to Visonic Alarm: %s", err, exc_info=True)
        raise ConfigEntryNotReady(f"Could not connect/login to Visonic Alarm: {err}") from err

    async def async_update_data() -> dict[str, Any]:
        """Fetch data from API."""
        global _last_devices_refresh

        try:
            # status often changes frequently
            await hass.async_add_executor_job(alarm.update_status)

            # devices/zone list changes rarely → refresh less often
            now = time.time()
            if (now - _last_devices_refresh) >= _DEVICES_REFRESH_SECONDS:
                _last_devices_refresh = now
                try:
                    await hass.async_add_executor_job(alarm.update_devices)
                except Exception as dev_err:
                    _LOGGER.debug("update_devices failed (ignored): %s", dev_err)

            devices = _extract_devices(alarm)

            # Helpful one-time-ish log if no devices found
            if not devices:
                _LOGGER.warning(
                    "No devices/zones found yet. If this persists, we may need to map the correct "
                    "attribute from the library. Alarm attrs sample: has contacts=%s devices=%s zones=%s",
                    hasattr(alarm, "contacts"),
                    hasattr(alarm, "devices"),
                    hasattr(alarm, "zones"),
                )

            return {
                "state": getattr(alarm, "state", None),
                "status": getattr(alarm, "status", None),
                "devices": devices,
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "alarm": alarm,
        "config": entry.data,
        "options": entry.options,
        "no_pin_required": no_pin_required,
        "event_hour_offset": event_hour_offset,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
