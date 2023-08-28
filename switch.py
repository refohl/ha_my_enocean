"""Support for EnOcean switches."""
import logging
import asyncio
import random

import voluptuous as vol

from homeassistant import helpers
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.core import callback
from homeassistant.const import (
    CONF_ID,
    CONF_NAME,
    CONF_SWITCHES,
    ATTR_DEVICE_CLASS,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .device import EnOceanDevice

from .const import DOMAIN
from .const import (
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NO_OF_CHANNELS,
    CONF_LOADED,
)
from .const import (
    DATA_BASE,
    DATA_DEVICES,
    DATA_DISPATCHERS,
)
from .const import DELAY_INIT
from .const import (
    ENOCEAN_SWITCH,
)
from .const import (
    SIGNAL_ADD_ENTITIES,
)
from .const import DEVICES_EEP

from enocean.protocol.constants import PACKET
from enocean.utils import combine_hex

_LOGGER = logging.getLogger(__name__)
'''
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Required(CONF_NAME, default=DEFAULT_CONF_NAME_SWITCH): cv.string,
        vol.Required(CONF_MANUFACTURER, default=DEFAULT_CONF_MANUFACTURER): cv.string,
        vol.Required(CONF_MODEL, default=DEFAULT_CONF_MODEL): cv.string,
        vol.Required(CONF_NO_OF_CHANNELS, default=DEFAULT_CONF_NO_OF_CHANNELS): cv.positive_int,
    }
)
'''

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the EnOcean switch platform."""
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up EnOcean Switch from Config Entry."""

    async def async_add_switches():
        devices = hass.data[DOMAIN][DATA_DEVICES]
        _LOGGER.debug(f"[async_add_switches()] devices: {devices}")
        for dev in devices.values():
            if CONF_SWITCHES in dev[ATTR_DEVICE_CLASS].keys():
                if not dev[CONF_LOADED]:
                    dev_id = dev[CONF_ID]
                    dev_manufacturer = dev[CONF_MANUFACTURER]
                    dev_model = dev[CONF_MODEL]
                    dev_no_of_channels = dev[ATTR_DEVICE_CLASS][CONF_SWITCHES][CONF_NO_OF_CHANNELS]
                    _LOGGER.debug(f"Class '{CONF_SWITCHES}' found for device id {dev_id}!")

                    # delay device initialization randomly within [0,DELAY_INIT) seconds to avoid conflicts/timeouts with many devices
                    rand_nb = random.random()*DELAY_INIT
                    await asyncio.sleep(rand_nb)
                    async_add_entities([
                        EnOceanSwitch(
                            dev_id=dev_id,
                            dev_name=f"{ENOCEAN_SWITCH}, ID [{', '.join([hex(x) for x in dev_id])}]",
                            dev_manufacturer=dev_manufacturer,
                            dev_model=dev_model,
                            dev_via_device=(DOMAIN, combine_hex(hass.data[DOMAIN][DATA_BASE][CONF_ID])),
                            dev_channel=dev_ch,
                        )
                        for dev_ch in range(0,dev_no_of_channels)
                    ])

                    hass.data[DOMAIN][DATA_DEVICES][combine_hex(dev_id)][CONF_LOADED] = True

    # Connect to signal to add devices
    unsubscribe_dispatcher = hass.helpers.dispatcher.async_dispatcher_connect(SIGNAL_ADD_ENTITIES, async_add_switches)
    hass.data[DOMAIN][DATA_DISPATCHERS].append(unsubscribe_dispatcher)


class EnOceanSwitch(EnOceanDevice, SwitchEntity):
    """Representation of an EnOcean switch device."""

    def __init__(
        self,
        dev_id,
        dev_name,
        dev_manufacturer,
        dev_model,
        dev_via_device,
        dev_channel
        ):
        """Initialize the EnOcean switch device."""
        super().__init__(
            dev_id=dev_id,
            dev_name=dev_name,
            dev_manufacturer=dev_manufacturer,
            dev_model=dev_model,
            dev_sw_version=None,
            dev_via_device=dev_via_device
        )
        self.dev_channel = dev_channel
        self._is_on = False

    @property
    def device_info(self):
        _LOGGER.debug("super().device_info: %s", super().device_info)
        self.dev_info = super().device_info
        #self.dev_info["channel"] = self.dev_channel
        return self.dev_info

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{combine_hex(self.dev_id)}-{self.dev_channel}"

    @property
    def name(self):
        """Name of the device."""
        return f"{self.dev_name}, CH{self.dev_channel}"
    
    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._is_on

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        """Request current status upon startup."""
        _LOGGER.debug(f"Request current status upon startup.")
        self.request_status()

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        dict_key = f"{self.dev_manufacturer}_{self.dev_model}"
        
        if "D2-01-00" in DEVICES_EEP[dict_key]:
            # D2-01-00, CMD 0x1
            # [Command ID] 
            cmd_id = 0x01
            # [Dim value] 0x00: Switch to new value
            dim_value = 0x00
            # [I/O channel]
            io_channel = self.dev_channel
            # [Output value] 0x00 -> OFF; 0x64 -> ON
            output_value = 0x64

            # Packet: data
            data = [0xD2]
            # DB_2
            data.extend([cmd_id])
            # DB_1
            data.extend([dim_value<<5 | io_channel])
            # DB_0
            data.extend([output_value])
            # Sender ID
            data.extend(self.hass.data[DOMAIN][DATA_BASE][CONF_ID])
            # Status
            data.extend([0x00])

        elif "A5-38-08" in DEVICES_EEP[dict_key]:
            # A5-38-08, CMD 0x1
            # [Command ID] 
            cmd_id = 0x01
            # [Time] 0x0000: 0 -> no time specified
            time = [0x00,0x00]
            # [Learn bit]: 0 -> Tech-in telegram
            lrn_bit = 0x01
            # [Lock/Unlock] 0 -> Unlock
            lck_bit = 0x00
            # [Delay/Duration] 0 -> Time=Duration
            del_bit = 0x00
            # [Switching Command] 1 -> On
            sw_bit = 0x01

            # Packet: data
            data = [0xA5]
            # DB_3
            data.extend([cmd_id])
            # DB_2/1
            data.extend(time)
            # DB_0
            data.extend([lrn_bit<<3 | lck_bit<<2 | del_bit<<1 | sw_bit])
            # Sender ID
            data.extend(self.hass.data[DOMAIN][DATA_BASE][CONF_ID])
            # Status
            data.extend([0x00])

        else:
            data = []

        # Packet: optional data (Packet Type 1: RADIO_ERP1)
        # [SubTelNum] Number of subtelegram; Send: 3 / receive: 0
        optional = [0x03]
        # [Destination ID] Broadcast transmission: FF FF FF FF
        optional.extend(self.dev_id)
        # [dBm] Send case: FF
        optional.extend([0xFF])
        # [Security Level] Send Case: Will be ignored
        optional.extend([0x00])

        # send command
        self.send_command(
            packet_type=0x01,
            data=data,
            optional=optional,
        )

        #self._is_on = True
        _LOGGER.debug(f"Switch CH{self.dev_channel} turned ON.")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        dict_key = f"{self.dev_manufacturer}_{self.dev_model}"
        
        if "D2-01-00" in DEVICES_EEP[dict_key]:
            # D2-01-00, CMD 0x1
            # [Command ID] 
            cmd_id = 0x01
            # [Dim value] 0x00: Switch to new value
            dim_value = 0x00
            # [I/O channel]
            io_channel = self.dev_channel
            # [Output value] 0x00 -> OFF; 0x64 -> ON
            output_value = 0x00

            # Packet: data
            data = [0xD2]
            # DB_2
            data.extend([cmd_id])
            # DB_1
            data.extend([dim_value<<5 | io_channel])
            # DB_0
            data.extend([output_value])
            # Sender ID
            data.extend(self.hass.data[DOMAIN][DATA_BASE][CONF_ID])
            # Status
            data.extend([0x00])

        elif "A5-38-08" in DEVICES_EEP[dict_key]:
            # A5-38-08, CMD 0x1
            # [Command ID] 
            cmd_id = 0x01
            # [Time] 0x0000: 0 -> no time specified
            time = [0x00,0x00]
            # [Learn bit]: 0 -> Tech-in telegram
            lrn_bit = 0x01
            # [Lock/Unlock] 0 -> Unlock
            lck_bit = 0x00
            # [Delay/Duration] 0 -> Time=Duration
            del_bit = 0x00
            # [Switching Command] 1 -> On
            sw_bit = 0x00

            # Packet: data
            data = [0xA5]
            # DB_3
            data.extend([cmd_id])
            # DB_2/1
            data.extend(time)
            # DB_0
            data.extend([lrn_bit<<3 | lck_bit<<2 | del_bit<<1 | sw_bit])
            # Sender ID
            data.extend(self.hass.data[DOMAIN][DATA_BASE][CONF_ID])
            # Status
            data.extend([0x00])

        else:
            data = []

        # Packet: optional data (Packet Type 1: RADIO_ERP1)
        # [SubTelNum] Number of subtelegram; Send: 3 / receive: 0
        optional = [0x03]
        # [Destination ID] Broadcast transmission: FF FF FF FF
        optional.extend(self.dev_id)
        # [dBm] Send case: FF
        optional.extend([0xFF])
        # [Security Level] Send Case: Will be ignored
        optional.extend([0x00])

        # send command
        self.send_command(
            packet_type=0x01,
            data=data,
            optional=optional,
        )
        
        #self._is_on = False
        _LOGGER.debug(f"Switch CH{self.dev_channel} turned OFF.")

    def packet_receiver(self, packet):
        """Update internal device state when receiving a status response."""
        super().packet_receiver(packet)
        dict_key = f"{self.dev_manufacturer}_{self.dev_model}"
        if packet.data[0]==0xD2:
            if "D2-01-00" in DEVICES_EEP[dict_key]:
                packet.parse_eep(rorg_func=0x01, rorg_type=0x01)
                if packet.parsed["CMD"]["raw_value"]==0x04:
                    _LOGGER.debug(f"[EnOceanSwitch.packet_receiver()] Status: {packet}")
                    channel = packet.parsed["IO"]["raw_value"]
                    output = packet.parsed["OV"]["raw_value"]
                    if channel==self.dev_channel:
                        self._is_on = (output > 0)
                        self.schedule_update_ha_state()
        elif packet.data[0]==0xF6:
            if "F6-02-01" in DEVICES_EEP[dict_key]:
                _LOGGER.debug(f"[EnOceanSwitch.packet_receiver()] Status: {packet}")
                if packet.data[1]==0x50:
                    self._is_on = False
                    self.schedule_update_ha_state()
                if packet.data[1]==0x70:
                    self._is_on = True
                    self.schedule_update_ha_state()
        elif packet.data[0]==0xA5:
            if "A5-11-04" in DEVICES_EEP[dict_key]:
                _LOGGER.debug(f"[EnOceanSwitch.packet_receiver()] Status: {packet}")
                if packet.data[1]==0x00:
                    self._is_on = False
                    self.schedule_update_ha_state()
                if packet.data[1]==0xFF:
                    self._is_on = True
                    self.schedule_update_ha_state()

    def request_status(self):
        dict_key = f"{self.dev_manufacturer}_{self.dev_model}"
        
        if "D2-01-00" in DEVICES_EEP[dict_key]:
            # D2-01, CMD 0x3
            # [Command ID] 
            cmd_id = 0x03
            # [I/O channel]
            io_channel = self.dev_channel

            # Packet: data
            data = [0xD2]
            # DB_1
            data.extend([cmd_id])
            # DB_0
            data.extend([io_channel])
            # Sender ID
            data.extend(self.hass.data[DOMAIN][DATA_BASE][CONF_ID])
            # Status
            data.extend([0x00])

            # Packet: optional data (Packet Type 1: RADIO_ERP1)
            # [SubTelNum] Number of subtelegram; Send: 3 / receive: 0
            optional = [0x03]
            # [Destination ID] Broadcast transmission: FF FF FF FF
            optional.extend(self.dev_id)
            # [dBm] Send case: FF
            optional.extend([0xFF])
            # [Security Level] Send Case: Will be ignored
            optional.extend([0x00])

            # send command
            self.send_command(
                packet_type=0x01,
                data=data,
                optional=optional,
            )

        elif "A5-38-08" in DEVICES_EEP[dict_key]:
            # Eltako devices do not support status requests
            # -> switch of upon startup to synchronize
            self.hass.async_create_task(
                self.async_turn_off()
            )

        else:
            pass

