"""Config flow for EnOcean integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_BASE,
    CONF_ID,
    CONF_NAME,
    ATTR_DEVICE_CLASS,
)

from .const import DOMAIN
from .const import (
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NO_OF_CHANNELS,
    CONF_SERIAL_PORT,
    CONF_OPTION,
)
from .const import (
    DEFAULT_CONF_HUB_SERIAL_PORT,
    DEFAULT_CONF_HUB_MANUFACTURER,
    DEFAULT_CONF_HUB_MODEL,
)
#from .const import (
#    OPTION_NONE,
#    OPTION_ADD_SWITCH,
#    OPTION_LIST,
#)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EnOcean."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN

    def __init__(self):
        self.base_id_int = 0

    #@staticmethod
    #@callback
    #def async_get_options_flow(config_entry):
    #    return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                return self.async_create_entry(
                    title=self.hass.config.location_name,
                    data={
                        CONF_ID: self.base_id_int,
                        CONF_MANUFACTURER: user_input[CONF_MANUFACTURER],
                        CONF_MODEL: user_input[CONF_MODEL],
                        ATTR_DEVICE_CLASS: {
                            CONF_BASE: {
                                CONF_SERIAL_PORT: user_input[CONF_SERIAL_PORT],
                            },
                        }
                    },
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        if DOMAIN in self.hass.data.keys():
            return self.async_abort(reason="already_configured")
        else:
            return self.async_show_form(
                step_id="user", 
                data_schema=vol.Schema(
                    {
                        # Specify items in the order they are to be displayed in the UI
                        vol.Required(CONF_MANUFACTURER, default=DEFAULT_CONF_HUB_MANUFACTURER): str,
                        vol.Required(CONF_MODEL, default=DEFAULT_CONF_HUB_MODEL): str,
                        vol.Required(CONF_SERIAL_PORT, default=DEFAULT_CONF_HUB_SERIAL_PORT): str,
                    }
                ), 
                errors=errors
            )

    async def async_step_import(self, user_input):
        """Handle EnOcean config import."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title=self.hass.config.location_name,
            data=user_input
        )
    

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
    _LOGGER.debug("CannotConnect")


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
    _LOGGER.debug("InvalidAuth")


#class OptionsFlowHandler(config_entries.OptionsFlow):
#
#    def __init__(self, config_entry):
#        """Initialize EnOcean options flow."""
#        self.config_entry = config_entry
#
#    async def async_step_init(self, user_input=None):
#        """Manage the options."""
#        
#        errors = {}
#        if user_input is not None:
#            #self.config_entry.options.update(user_input)
#            #_LOGGER.exception("Option config entry: %s", self.config_entry.options)
#            ##return self.async_create_entry(
#            ##    title="",
#            ##    data={
#            ##        CONF_OPTION: user_input[CONF_OPTION],
#            ##    }
#            ##)
#            if user_input[CONF_OPTION]==OPTION_ADD_SWITCH:
#                return await self.async_step_config_switch()
#
#        return self.async_show_form(
#            step_id="init",
#            data_schema=vol.Schema(
#                {
#                    vol.Required(
#                        CONF_OPTION,
#                        default=self.config_entry.options.get(
#                            CONF_OPTION, [OPTION_NONE]
#                        ),
#                    ): vol.In(OPTION_LIST),
#
#                }
#            ),
#            errors=errors
#        )
#

