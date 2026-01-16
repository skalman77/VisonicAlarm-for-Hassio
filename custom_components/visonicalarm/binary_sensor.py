"""Binary sensors for Visonic Alarm zones (classified by subtype, strict mapping)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Exact subtype sets seen in your system (plus safe extras)
OPENING_SUBTYPES = {
    "CONTACT",
    "CONTACT_AUX",
    "MC303_VANISH",
    "DOOR",
    "WINDOW",
    "MAGNET",
    "REED",
}
MOTION_SUBTYPES = {
    "MOTION",
    "FLAT_PIR_SMART",
    "PIR",
    "PIR_SMART",
    "CURTAIN_PIR",
    "MOTION_DETECTOR",
}
SMOKE_SUBTYPES = {
    "SMOKE",
    "SMOKE_DETECTOR",
    "FIRE",
    "HEAT",
    "CO",
}


def _get(obj: Any, *keys: str, default=None):
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] is not None:
                return obj[k]
    for k in keys:
        if hasattr(obj, k):
            v = getattr(obj, k)
            if v is not None:
                return v
    return default


def _device_type(obj: Any) -> str:
    t = _get(obj, "device_type", "type", "_Device__device_type", default="")
    return str(t).strip().upper() if t is not None else ""


def _zone_id(zone: Any) -> str:
    return str(_get(zone, "id", "zone_id", "device_id", "_Device__id", default=""))


def _device_number(zone: Any) -> str:
    dn = _get(zone, "device_number", "_Device__device_number", "number", default=None)
    return "" if dn is None else str(dn)


def _zone_name(zone: Any) -> str:
    name = _get(zone, "name", "label", "_Device__name", default="")
    name = str(name).strip() if name is not None else ""
    zid = _zone_id(zone) or "unknown"
    return name if name else f"Zone {zid}"


def _zone_subtype(zone: Any) -> str:
    st = _get(zone, "subtype", "_Device__subtype", default="")
    return str(st).strip().upper() if st is not None else ""


def _truthy(v: Any) -> bool | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "on", "open", "opened", "alarm", "triggered", "detected", "fault"):
            return True
        if s in ("0", "false", "off", "closed", "clear", "ok", "ready", "normal"):
            return False
    return None


def _parse_warnings(w: Any) -> dict[str, Any]:
    if w is None:
        return {}
    if isinstance(w, dict):
        return w
    if isinstance(w, list):
        out: dict[str, Any] = {}
        for item in w:
            if isinstance(item, dict):
                out.update(item)
            elif isinstance(item, str):
                out[item] = True
        return out
    if isinstance(w, str):
        return {w: True}
    return {"repr": repr(w)}


def _zone_is_on(zone: Any) -> bool | None:
    for key in ("open", "is_open", "isOpen", "triggered", "is_triggered", "alarm", "fault"):
        v = _truthy(_get(zone, key, default=None))
        if v is not None:
            return v

    v = _truthy(_get(zone, "state", "status", default=None))
    if v is not None:
        return v

    warnings = _parse_warnings(_get(zone, "warnings", "_Device__warnings", default=None))
    for k in ("open", "opened", "alarm", "triggered", "detected", "fault", "tamper"):
        if k in warnings:
            vv = _truthy(warnings.get(k))
            return True if vv is None else vv

    return None


def _device_class_from_subtype(subtype: str) -> BinarySensorDeviceClass:
    """
    STRICT mapping with correct precedence:
    CONTACT must NEVER end up as SMOKE.
    """
    st = (subtype or "").strip().upper()

    # 1) Opening/contact first (your case)
    if st in OPENING_SUBTYPES:
        return BinarySensorDeviceClass.OPENING
    if "CONTACT" in st or "VANISH" in st or "DOOR" in st or "WINDOW" in st:
        return BinarySensorDeviceClass.OPENING

    # 2) Motion
    if st in MOTION_SUBTYPES:
        return BinarySensorDeviceClass.MOTION
    if "PIR" in st or "MOTION" in st:
        return BinarySensorDeviceClass.MOTION

    # 3) Smoke/fire
    if st in SMOKE_SUBTYPES:
        return BinarySensorDeviceClass.SMOKE
    if "SMOKE" in st or "FIRE" in st or "HEAT" in st or st == "CO":
        return BinarySensorDeviceClass.SMOKE

    # Default
    return BinarySensorDeviceClass.OPENING


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    devices = (coordinator.data or {}).get("devices", []) or []
    zones = [d for d in devices if _device_type(d) == "ZONE"]

    if not zones:
        _LOGGER.warning("No ZONE devices found; binary sensors will not be created.")
        return

    entities: list[BinarySensorEntity] = [VisonicZoneBinarySensor(coordinator, z) for z in zones]
    async_add_entities(entities, update_before_add=True)


class VisonicZoneBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, zone: Any) -> None:
        super().__init__(coordinator)

        zid = _zone_id(zone) or "unknown"
        dnum = _device_number(zone)
        st = _zone_subtype(zone) or "UNKNOWN"

        unique_tail = f"{zid}_{st}"
        if dnum not in ("", "None", "null"):
            unique_tail = f"{unique_tail}_{dnum}"

        self._zone_id = zid
        self._device_number = dnum
        self._subtype = st

        self._attr_unique_id = f"{DOMAIN}_zone_{unique_tail}"
        self._attr_name = _zone_name(zone)
        self._attr_device_class = _device_class_from_subtype(st)

        _LOGGER.debug(
            "Zone created: id=%s subtype=%s device_class=%s",
            self._zone_id,
            self._subtype,
            self._attr_device_class,
        )

    @property
    def is_on(self) -> bool | None:
        devices = (self.coordinator.data or {}).get("devices", []) or []
        for z in devices:
            if _device_type(z) != "ZONE":
                continue
            if _zone_id(z) != self._zone_id:
                continue
            if _zone_subtype(z) and _zone_subtype(z) != self._subtype:
                continue
            if self._device_number and _device_number(z) and _device_number(z) != self._device_number:
                continue
            return _zone_is_on(z)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        devices = (self.coordinator.data or {}).get("devices", []) or []
        for z in devices:
            if _device_type(z) != "ZONE":
                continue
            if _zone_id(z) != self._zone_id:
                continue
            if _zone_subtype(z) and _zone_subtype(z) != self._subtype:
                continue
            if self._device_number and _device_number(z) and _device_number(z) != self._device_number:
                continue
            return {
                "subtype": _zone_subtype(z),
                "device_type": _device_type(z),
                "device_number": _device_number(z) or None,
                "warnings": _get(z, "warnings", "_Device__warnings", default=None),
                "zone_group": _get(z, "zone", "_Device__zone", default=None),
            }
        return {}
