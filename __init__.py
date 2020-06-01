"""The EnOcean integration."""
import logging
import asyncio
import os

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_BASE,
    CONF_SWITCHES,
    CONF_ID,
    CONF_NAME,
    ATTR_DEVICE_CLASS,
)

from .const import DOMAIN
from .const import (
    CONF_ENTRY_ID, 
    CONF_SERIAL_PORT,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_VIA_DEVICE,
    CONF_NO_OF_CHANNELS,
    CONF_LOADED,
)
from .const import (
    DEFAULT_DATABASE_NAME,
)
from .const import (
    DATA_BASE,
    DATA_CONFIG,
    DATA_DEVICES,
    DATA_DISPATCHERS,
    DATA_DONGLE,
    DATA_PLATFORM,
)
from .const import (
    ENOCEAN_TRANSCEIVER,
)
from .const import (
    RETURN_DB_NEW,
    RETURN_DB_EXISTING,
)
from .const import (
    SIGNAL_TEACH_IN,
    SIGNAL_ADD_ENTITIES,
)
from .const import (
    SERVICE_TEACH_IN,
    SERVICE_ADD_SWITCH,
    SERVICE_REMOVE_DEVICE,
)
from .database import *
from .device import EnOceanDevice, EnOceanDongle
from .switch import EnOceanSwitch

from enocean.utils import combine_hex

_LOGGER = logging.getLogger(__name__)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS = ["switch"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the EnOcean component."""
    
    _LOGGER.debug("[async_setup()] Start up")
    #for cf in hass.config_entries._entries:
    #    _LOGGER.debug(f"ConfigEntry: {cf}")
    #    _LOGGER.debug(f"version: {cf.version}")
    #    _LOGGER.debug(f"domain: {cf.domain}")
    #    _LOGGER.debug(f"title: {cf.title}")
    #    _LOGGER.debug(f"data: {cf.data}")
    #    _LOGGER.debug(f"source: {cf.source}")
    #    _LOGGER.debug(f"connection_class: {cf.connection_class}")
    #    _LOGGER.debug(f"system_options: {cf.system_options}")
    #    _LOGGER.debug(f"options: {cf.options}")
    #    _LOGGER.debug(f"unique_id: {cf.unique_id}")
    #    _LOGGER.debug(f"entry_id: {cf.entry_id}")
    #    _LOGGER.debug(f"state: {cf.state}")
    #_LOGGER.debug(f"hass.data.keys(): {hass.data.keys()}")
    #_LOGGER.debug(f"hass.data['custom_components'].keys(): {hass.data['custom_components'].keys()}")
    #_LOGGER.debug(f"hass.data['integrations']: {hass.data['integrations']}")
    #_LOGGER.debug(f"[async_setup()] hass.config_entries.async_entries(DOMAIN): {hass.config_entries.async_entries(DOMAIN)}")
    ##hass.config_entries.async_entries(DOMAIN)[0].async_unload_entry()
    ##_LOGGER.debug(f"[async_setup()] hass.config_entries.async_entries(DOMAIN): {hass.config_entries.async_entries(DOMAIN)}")
    #dreg = await hass.helpers.device_registry.async_get_registry()
    #_LOGGER.debug(f"dreg.devices.values(): {dreg.devices.values()}")
    ##dreg.async_remove_device(device_id='13637dae238d4d618a80470b44533c31')
    ##_LOGGER.debug(f"dreg.devices.values(): {dreg.devices.values()}")
    
    hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        _LOGGER.debug("No manual EnOcean platform config available.")
        return True

    if not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data={
                    CONF_MANUFACTURER: config[DOMAIN].get(CONF_MANUFACTURER),
                    CONF_MODEL: config[DOMAIN].get(CONF_MODEL),
                    ATTR_DEVICE_CLASS: {
                        CONF_BASE: {
                            CONF_SERIAL_PORT: config[DOMAIN].get(CONF_SERIAL_PORT),
                        },
                    }
                },
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up EnOcean from a config entry."""
    _LOGGER.debug(f"[async_setup_entry()] config_entry.data: {config_entry.data}")
    _LOGGER.debug(f"[async_setup_entry()] config_entry.options: {config_entry.options}")

    if DOMAIN not in hass.data.keys():
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][DATA_DISPATCHERS] = []

    """Set up EnOcean Hub from Config Entry."""
    _LOGGER.debug(f"Class '{CONF_BASE}' found in config_entry attributes!")

    """Set up the EnOcean hub."""
    dongle = EnOceanDongle(
        hass, 
        config_entry.data[ATTR_DEVICE_CLASS][CONF_BASE][CONF_SERIAL_PORT]
    )
    hass.data[DOMAIN][DATA_DONGLE] = dongle
    _LOGGER.debug(f"[async_setup_entry()] dongle.dev_id: {dongle.dev_id}")

    dreg = await hass.helpers.device_registry.async_get_registry()
    dreg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        name=f"{ENOCEAN_TRANSCEIVER}, ID [{', '.join([hex(x) for x in dongle.dev_id])}]",
        connections=None,
        identifiers={(DOMAIN, combine_hex(dongle.dev_id))},
        manufacturer=config_entry.data[CONF_MANUFACTURER],
        model=config_entry.data[CONF_MODEL],
        sw_version=None,
        via_device=None,
    )

    # get device object for hub
    device = dreg.async_get_device({(DOMAIN, combine_hex(dongle.dev_id))}, set())

    hass.data[DOMAIN][DATA_BASE] = {
        CONF_ENTRY_ID: config_entry.entry_id,
        CONF_ID: dongle.dev_id,
    }

    database_name = DEFAULT_DATABASE_NAME
    db_file = os.path.join(hass.config.config_dir, database_name)
    db_state = database_init(hass, db_file)
    dev_data = {
        CONF_ID: dongle.dev_id,
        CONF_MANUFACTURER: config_entry.data[CONF_MANUFACTURER],
        CONF_MODEL: config_entry.data[CONF_MODEL],
        CONF_LOADED: True,
        ATTR_DEVICE_CLASS: config_entry.data[ATTR_DEVICE_CLASS],
    }
    
    if db_state==RETURN_DB_NEW:
        database_add_device(db_file, dev_data)
    elif db_state==RETURN_DB_EXISTING:
        database_update_hub(db_file, dev_data)

    hass.data[DOMAIN][DATA_DEVICES] = {}
    dev_all = database_get_device(db_file, [0xFF,0xFF,0xFF,0xFF])
    for dev in dev_all:
        dev[CONF_LOADED] = False
        hass.data[DOMAIN][DATA_DEVICES][combine_hex(dev[CONF_ID])] = dev
    _LOGGER.debug(f"[async_setup_entry()] dev_all: {hass.data[DOMAIN][DATA_DEVICES]}")

    to_setup = []
    for component in PLATFORMS:
        task = hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )
        to_setup.append(task)
    hass.data[DOMAIN][DATA_PLATFORM] = to_setup
    _LOGGER.debug(f"[async_setup_entry()] to_setup: {to_setup}")

    asyncio.create_task(async_load_entities(hass))
    
    #config_entry.add_update_listener(update_listener)

    def handle_service_teach_in(call):
        dev_id = call.data.get("dev_id")
        dev_id = [int(x,0) for x in dev_id[1:-1].split(",")]
        _LOGGER.debug(f"[handle_service_teach_in]: {dev_id}")
        hass.helpers.dispatcher.dispatcher_send(SIGNAL_TEACH_IN, dev_id)
        
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_TEACH_IN,
        service_func=handle_service_teach_in,
        schema=vol.Schema(
            {
                vol.Required("dev_id"): str,
            }
        ),
    )

    def handle_service_add_switch(call):
        dev_data = {
            CONF_ID: [int(x,0) for x in call.data.get("dev_id")[1:-1].split(",")],
            CONF_NAME: None,
            CONF_MANUFACTURER: call.data.get("dev_manufacturer"),
            CONF_MODEL: call.data.get("dev_model"),
            CONF_VIA_DEVICE: hass.data[DOMAIN][DATA_BASE][CONF_ID],
            CONF_LOADED: False,
            ATTR_DEVICE_CLASS: {
                CONF_SWITCHES: {
                    CONF_NO_OF_CHANNELS: call.data.get("dev_no_of_channels"),
                },
            }
        }
        _LOGGER.debug(f"[handle_service_add_switch()] dev_data: {dev_data}")
        hass.data[DOMAIN][DATA_DEVICES][combine_hex(dev[CONF_ID])] = dev_data
        hass.helpers.dispatcher.async_dispatcher_send(SIGNAL_ADD_ENTITIES)
        database_add_device(db_file, dev_data)
        
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_ADD_SWITCH,
        service_func=handle_service_add_switch,
        schema=vol.Schema(
            {
                vol.Required("dev_id"): str,
                vol.Required("dev_manufacturer"): str,
                vol.Required("dev_model"): str,
                vol.Required("dev_no_of_channels"): int,
            }
        ),
    )

    def handle_service_remove_device(call):
        dev_id = call.data.get("dev_id")
        dev_id = [int(x,0) for x in dev_id[1:-1].split(",")]

        dreg = asyncio.run_coroutine_threadsafe( hass.helpers.device_registry.async_get_registry() , hass.loop).result()
        dreg_dev = dreg.async_get_device({(DOMAIN, combine_hex(dev_id))}, set())
        dreg.async_remove_device(device_id=dreg_dev.id)
        
        hass.data[DOMAIN][DATA_DEVICES].pop(combine_hex(dev[CONF_ID]))
        
        database_remove_device(db_file, dev_id)
        
    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_REMOVE_DEVICE,
        service_func=handle_service_remove_device,
        schema=vol.Schema(
            {
                vol.Required("dev_id"): str,
            }
        ),
    )

    return True


async def async_load_entities(hass: HomeAssistant) -> None:
    """Load entities after integration was setup."""
    to_setup = hass.data[DOMAIN][DATA_PLATFORM]
    results = await asyncio.gather(*to_setup, return_exceptions=True)
    _LOGGER.debug(f"create_task, results: {results}")
    for res in results:
        if isinstance(res, Exception):
            _LOGGER.warning("Couldn't setup EnOcean platform: %s", res)
    hass.helpers.dispatcher.async_dispatcher_send(SIGNAL_ADD_ENTITIES)


#async def update_listener(hass, config_entry):
#    _LOGGER.debug(f"update_listener() called")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        """Remove devices from device registry."""
        dreg = await hass.helpers.device_registry.async_get_registry()
        for dev_id in hass.data[DOMAIN][DATA_DEVICES].keys():
            dreg_dev = dreg.async_get_device({(DOMAIN, dev_id)}, set())
            dreg.async_remove_device(device_id=dreg_dev.id)
        
        """Unsubscribe registered signals."""
        unsubscribe_dispatchers = hass.data[DOMAIN][DATA_DISPATCHERS]
        for usd in unsubscribe_dispatchers:
            usd()
        
        """Close serial communication channel."""
        hass.data[DOMAIN][DATA_DONGLE].communicator.stop()

        """Remove data from homeassistant data."""
        hass.data.pop(DOMAIN)

    return unload_ok
