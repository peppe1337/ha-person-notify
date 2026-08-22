"""Config Flow fuer person_notify."""
from __future__ import annotations

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN


class PersonNotifyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config Flow fuer person_notify — eine Instanz, keine Eingabe noetig."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Einziger Schritt: Bestaetigung."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Person Notify", data={})

        return self.async_show_form(step_id="user")
