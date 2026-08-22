"""person_notify — Pro Person eine NotifyEntity, die Mobilgeraete automatisch aufloest."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_state_added_domain,
    async_track_state_removed_domain,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NOTIFY]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration einrichten."""
    _LOGGER.debug("person_notify: async_setup_entry gestartet")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _async_person_added(event: Event) -> None:
        """Config-Entry neu laden wenn eine Person-Entitaet hinzukommt."""
        _LOGGER.debug(
            "person_notify: Person-Entitaet hinzugekommen (%s), Entry wird neu geladen",
            event.data.get("entity_id"),
        )
        hass.async_create_task(
            hass.config_entries.async_reload(entry.entry_id)
        )

    @callback
    def _async_person_removed(event: Event) -> None:
        """Config-Entry neu laden wenn eine Person-Entitaet entfernt wird."""
        _LOGGER.debug(
            "person_notify: Person-Entitaet entfernt (%s), Entry wird neu geladen",
            event.data.get("entity_id"),
        )
        hass.async_create_task(
            hass.config_entries.async_reload(entry.entry_id)
        )

    # Beide Helfer aus homeassistant.helpers.event filtern auf Domain-Ebene —
    # kein globaler Listener mehr (event.py Zeilen 653 und 711, HA 2026.2.3).
    entry.async_on_unload(
        async_track_state_added_domain(hass, "person", _async_person_added)
    )
    entry.async_on_unload(
        async_track_state_removed_domain(hass, "person", _async_person_removed)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration entladen."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
