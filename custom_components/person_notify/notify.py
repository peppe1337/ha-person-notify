"""notify-Platform fuer person_notify."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import (
    SIGNAL_CONFIG_ENTRY_CHANGED,
    ConfigEntry,
    ConfigEntryChange,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Fuer jede Person-Entitaet eine NotifyEntity anlegen."""
    entities: list[PersonNotifyEntity] = []

    for state in hass.states.async_all("person"):
        entities.append(PersonNotifyEntity(hass, state.entity_id))

    if entities:
        async_add_entities(entities)
        _LOGGER.debug(
            "person_notify: %d Entitaeten angelegt: %s",
            len(entities),
            [e.entity_id for e in entities],
        )


def _resolve_targets(hass: HomeAssistant, person_entity_id: str) -> tuple[list[str], list[str]]:
    """Loest die Aufloesungskette fuer eine Person auf.

    Gibt (resolved_targets, unresolved_trackers) zurueck.
    resolved_targets: Liste der aufrufbaren mobile_app-Notify-Service-Namen.
    unresolved_trackers: Tracker ohne device_id (nicht aufloesbar).
    """
    state = hass.states.get(person_entity_id)
    if state is None:
        return [], []

    device_trackers: list[str] = state.attributes.get("device_trackers", [])
    if not device_trackers:
        return [], []

    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)

    resolved: list[str] = []
    unresolved: list[str] = []

    for tracker_id in device_trackers:
        entry = entity_reg.async_get(tracker_id)
        if entry is None or not entry.device_id:
            _LOGGER.debug(
                "person_notify: Tracker %s hat keine device_id (not in entity_registry oder kein Device) — uebersprungen",
                tracker_id,
            )
            unresolved.append(tracker_id)
            continue

        device = device_reg.async_get(entry.device_id)
        if device is None:
            _LOGGER.debug(
                "person_notify: Device %s nicht in device_registry gefunden — uebersprungen",
                entry.device_id,
            )
            unresolved.append(tracker_id)
            continue

        mobile_app_entry_id: str | None = None
        for config_entry_id in device.config_entries:
            ce = hass.config_entries.async_get_entry(config_entry_id)
            if ce is not None and ce.domain == "mobile_app":
                mobile_app_entry_id = config_entry_id
                break

        if mobile_app_entry_id is None:
            _LOGGER.debug(
                "person_notify: Kein mobile_app-ConfigEntry fuer Device %s von Tracker %s — uebersprungen",
                entry.device_id,
                tracker_id,
            )
            unresolved.append(tracker_id)
            continue

        ce = hass.config_entries.async_get_entry(mobile_app_entry_id)
        device_name = ce.data.get("device_name")
        if not device_name:
            _LOGGER.warning(
                "person_notify: mobile_app-ConfigEntry %s hat kein 'device_name' — uebersprungen",
                mobile_app_entry_id,
            )
            unresolved.append(tracker_id)
            continue

        service_name = slugify(f"mobile_app_{device_name}")
        resolved.append(service_name)
        _LOGGER.debug(
            "person_notify: Tracker %s -> mobile_app-Service notify.%s",
            tracker_id,
            service_name,
        )

    return resolved, unresolved


class PersonNotifyEntity(NotifyEntity):
    """Eine Benachrichtigungs-Entitaet fuer eine Person."""

    _attr_has_entity_name = True
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, hass: HomeAssistant, person_entity_id: str) -> None:
        """Initialisierung."""
        self.hass = hass
        self._person_entity_id = person_entity_id
        # z.B. person.max_mustermann -> max_mustermann
        object_id = person_entity_id.split(".", 1)[1]
        self._attr_unique_id = f"person_notify_{person_entity_id}"
        self._attr_name = f"Person Notify {object_id}"
        self._attr_extra_state_attributes: dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        """Ziele aufloesen und auf Aenderungen der Aufloesungskette hoeren."""
        await super().async_added_to_hass()
        self._update_targets()

        # Jedes Glied der Kette kann sich aendern, ohne dass gesendet wird:
        # device_trackers der Person, Tracker -> device_id (Entity-Registry),
        # Device -> Config-Entries (Device-Registry) und der device_name im
        # mobile_app-ConfigEntry (Umbenennung in der App).
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._person_entity_id], self._async_person_changed
            )
        )
        self.async_on_remove(
            self.hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED, self._async_refresh_targets
            )
        )
        self.async_on_remove(
            self.hass.bus.async_listen(
                dr.EVENT_DEVICE_REGISTRY_UPDATED, self._async_refresh_targets
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_CONFIG_ENTRY_CHANGED, self._async_config_entry_changed
            )
        )

    def _update_targets(self) -> bool:
        """Ziele neu aufloesen und als Attribute zwischenspeichern.

        Gibt True zurueck, wenn sich resolved_targets oder unresolved_trackers
        geaendert haben.
        """
        resolved, unresolved = _resolve_targets(self.hass, self._person_entity_id)
        attributes = {
            "resolved_targets": resolved,
            "unresolved_trackers": unresolved,
        }
        if attributes == self._attr_extra_state_attributes:
            return False
        self._attr_extra_state_attributes = attributes
        return True

    @callback
    def _async_refresh_targets(self, *_: Any) -> None:
        """State nur schreiben, wenn sich das Aufloesungsergebnis geaendert hat."""
        if self._update_targets():
            self.async_write_ha_state()

    @callback
    def _async_person_changed(self, event: Event[EventStateChangedData]) -> None:
        """Nur reagieren, wenn sich die device_trackers der Person geaendert haben.

        Die Person aendert ihren State bei jedem Standort-Update ihrer Tracker.
        """
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        old_trackers = old_state.attributes.get("device_trackers") if old_state else None
        new_trackers = new_state.attributes.get("device_trackers") if new_state else None
        if old_trackers != new_trackers:
            self._async_refresh_targets()

    @callback
    def _async_config_entry_changed(
        self, change: ConfigEntryChange, entry: ConfigEntry
    ) -> None:
        """Nur mobile_app-ConfigEntries gehoeren zur Aufloesungskette."""
        if entry.domain == "mobile_app":
            self._async_refresh_targets()

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Nachricht an alle aufloesbare Geraete der Person senden."""
        # Zur Sendezeit immer frisch aufloesen, nicht aus dem Cache.
        self._async_refresh_targets()
        resolved = self._attr_extra_state_attributes["resolved_targets"]
        unresolved = self._attr_extra_state_attributes["unresolved_trackers"]

        if not resolved:
            state = self.hass.states.get(self._person_entity_id)
            trackers = state.attributes.get("device_trackers", []) if state else []
            if not trackers:
                raise HomeAssistantError(
                    f"Person '{self._person_entity_id}' hat keine device_trackers. "
                    "Bitte der Person ein Mobilgeraet zuordnen."
                )
            raise HomeAssistantError(
                f"Fuer Person '{self._person_entity_id}' konnten keine mobile_app-Notify-Services "
                f"aufgeloest werden. "
                f"Nicht aufloesbare Tracker (kein mobile_app-Device): {unresolved}. "
                "Moegliche Gruende: Tracker stammt aus known_devices.yaml, Traccar oder GPS-Logger "
                "(kein device_id-Eintrag in der Entity-Registry)."
            )

        service_data: dict[str, Any] = {"message": message}
        if title is not None:
            service_data["title"] = title

        errors: list[str] = []
        called: list[str] = []
        for service_name in resolved:
            try:
                await self.hass.services.async_call(
                    "notify",
                    service_name,
                    service_data,
                    blocking=True,
                )
                called.append(service_name)
                _LOGGER.debug(
                    "person_notify: notify.%s fuer %s erfolgreich aufgerufen",
                    service_name,
                    self._person_entity_id,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{service_name}: {exc}")
                _LOGGER.error(
                    "person_notify: Fehler beim Aufruf von notify.%s: %s",
                    service_name,
                    exc,
                )

        if errors and not called:
            raise HomeAssistantError(
                f"Alle Benachrichtigungsversuche fuer '{self._person_entity_id}' fehlgeschlagen: "
                + "; ".join(errors)
            )
