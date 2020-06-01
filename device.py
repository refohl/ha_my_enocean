"""The EnOcean integration."""
import logging
import asyncio
import os

import voluptuous as vol

from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    CONF_ID,
    CONF_NAME,
)

from .const import DOMAIN
from .const import (
    DATA_BASE,
    DATA_DISPATCHERS,
)
from .const import (
    SIGNAL_RECEIVE_PACKET,
    SIGNAL_SEND_PACKET,
    SIGNAL_TEACH_IN,
)

from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.constants import RETURN_CODE
from enocean.protocol.packet import Packet, RadioPacket, ResponsePacket
from enocean.utils import combine_hex

_LOGGER = logging.getLogger(__name__)


class EnOceanDevice(Entity):
    """Parent class for all devices associated with the EnOcean component."""

    def __init__(
        self, 
        dev_id=None, 
        dev_name=None, 
        dev_manufacturer=None, 
        dev_model=None, 
        dev_sw_version=None, 
        dev_via_device=None
        ):
        """Initialize the device."""
        self.dev_id = dev_id
        self.dev_name = dev_name
        self.dev_manufacturer = dev_manufacturer
        self.dev_model = dev_model
        self.dev_sw_version = dev_sw_version
        self.dev_via_device = dev_via_device

    @property
    def device_info(self):
        _LOGGER.debug(self.hass.data[DOMAIN].keys())
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, combine_hex(self.dev_id))
            },
            "name": self.dev_name,
            "manufacturer": self.dev_manufacturer,
            "model": self.dev_model,
            "sw_version": self.dev_sw_version,
            "via_device": self.dev_via_device,
        }
    
    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{combine_hex(self.dev_id)}"
    
    async def async_added_to_hass(self):
        """Register callbacks."""
        unsubscribe_dispatcher = self.hass.helpers.dispatcher.async_dispatcher_connect(
            SIGNAL_RECEIVE_PACKET, self._packet_received_callback
        )
        self.hass.data[DOMAIN][DATA_DISPATCHERS].append(unsubscribe_dispatcher)
        
        unsubscribe_dispatcher = self.hass.helpers.dispatcher.async_dispatcher_connect(
            SIGNAL_TEACH_IN, self._teach_in_callback
        )
        self.hass.data[DOMAIN][DATA_DISPATCHERS].append(unsubscribe_dispatcher)

    def _packet_received_callback(self, packet):
        """Handle incoming packets."""
        if packet.sender_int == combine_hex(self.dev_id):
            self.packet_receiver(packet)

    def packet_receiver(self, packet):
        """Update internal state of the device when a packet arrives."""
        if packet.data[0]==0xD4:
            # Universal Teach-in Response (UTE)
            
            # [Uni-/bi-directional communication (EEP operation)] 0x01: Bidirectional communication
            eep_op = 0x01
            # [EEP Teach-in response message expected] 0x00: Not used
            teach_in_response = 0x00
            # [Teach-in request] 0x01: Request accepted, teach-in successful
            teach_in_request = 0x01
            # [Command identifier] 0x00: EEP Teach-in query, 0x01: Response
            cmd_iden = 0x01
            # [Number of individual channels to be taught in] 0x01: 1, 0xFF: all channels
            #no_of_ch = 0x01
            no_of_ch = packet.data[2]
            # [Manufacturer ID (LSB)]
            #man_id_lsb = 0x46
            man_id_lsb = packet.data[3]
            # [Manufacturer ID (MSB)]
            #man_id_msb = 0x00
            man_id_msb = packet.data[4]
            # [TYPE]
            #dev_type = 0x0F
            dev_type = packet.data[5]
            # [FUNC]
            #dev_func = 0x01
            dev_func = packet.data[6]
            # [RORG]
            #dev_rorg = 0xD2
            dev_rorg = packet.data[7]
            
            
            # Packet: data
            data = [0xD4]
            # DB_6
            data.extend([eep_op<<7 | teach_in_response<<6 | teach_in_request<<4 | cmd_iden])
            # DB_5
            data.extend([no_of_ch])
            # DB_4
            data.extend([man_id_lsb])
            # DB_3
            data.extend([man_id_msb])
            # DB_2
            data.extend([dev_type])
            # DB_1
            data.extend([dev_func])
            # DB_0
            data.extend([dev_rorg])
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

            _LOGGER.debug(f"[EnOceanDevice.packet_receiver]: UTE Response sent to {self.dev_id}")

    
    def _teach_in_callback(self, dev_id):
        """Handle teach in."""
        if combine_hex(dev_id) == combine_hex(self.dev_id):
            self.teach_in()

    def teach_in(self):
        """Send teach in command."""
        if ("NodOn" in self.dev_manufacturer) and ("SIN" in self.dev_model):
            # Supports UTE, handled in packet_receiver()
            pass

        elif ("Eltako" in self.dev_manufacturer) and ("FSR61" in self.dev_model):
            # 4BS Teach-in
            
            # Packet: data
            data = [0xA5]
            # DB_3
            data.extend([0xE0])
            # DB_2
            data.extend([0x40])
            # DB_1
            data.extend([0x0D])
            # DB_0
            data.extend([0x80])
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

        _LOGGER.debug(f"[EnOceanDevice.teach_in]: Sent to {self.dev_id}")

    def send_command(self, packet_type, data, optional):
        """Send a command via the EnOcean dongle."""
        packet = Packet(packet_type, data=data, optional=optional)
        self.hass.helpers.dispatcher.dispatcher_send(SIGNAL_SEND_PACKET, packet)


class EnOceanDongle(EnOceanDevice):
    """Representation of an EnOcean dongle."""

    def __init__(self, hass, ser):
        """Initialize the EnOcean dongle."""
        super().__init__(self)
        self.hass = hass
        self.ser = ser
        self.communicator = None

        """Connect to serial port of the EnOcean dongle."""
        self.communicator = SerialCommunicator(
            port=self.ser,
            callback=self.communicator_callback
        )
        # switch off automated teach-in, as it gets caught in infinite loop for UTE
        self.communicator.teach_in = False
        self.communicator.start()
        self.dev_id = self.communicator.base_id
        _LOGGER.debug(f"[EnOceanDongle] self.dev_id: {self.dev_id}")

        unsubscribe_dispatcher = self.hass.helpers.dispatcher.async_dispatcher_connect(
            SIGNAL_SEND_PACKET, self.send_packet
        )
        self.hass.data[DOMAIN][DATA_DISPATCHERS].append(unsubscribe_dispatcher)
    
    def send_packet(self, packet):
        """Send command through EnOcean dongle."""
        _LOGGER.debug(f"[EnOceanDongle.send_packet()] Sending packet: {packet}")
        self.communicator.send(packet)
        # Wait for response (acknowledgement): EnOcean defines timeout after 500ms
        packet = self.communicator.receive.get(block=True, timeout=0.5)
        if packet.response==RETURN_CODE.OK:
            _LOGGER.debug(f"[EnOceanDongle.send_packet()] Packet successfully sent")
        else:
            _LOGGER.debug(f"[EnOceanDongle.send_packet()] Error in sending packet")

    def communicator_callback(self, packet):
        """Handle EnOcean device's callback.

        This is the callback function called by python-enocan whenever there
        is an incoming packet.
        """
        if isinstance(packet, ResponsePacket):
            # The callback routine does not care about response packets (acknowledgements).
            # Put the packet back into the queue, so the sender can care and respect timeouts.
            _LOGGER.debug(f"[EnOceanDongle.communicator_callback()] ResponsePacket received: {packet}")
            self.communicator.receive.put(packet)
        if isinstance(packet, RadioPacket):
            # Emit signal for each radio packet to notify the addressed device.
            _LOGGER.debug(f"[EnOceanDongle.communicator_callback()] RadioPacket received: {packet}")
            self.hass.helpers.dispatcher.dispatcher_send(SIGNAL_RECEIVE_PACKET, packet)
    
    async def async_update_device_registry(self) -> None:
        """Add a device for this hub to the device registry."""
        dreg = await device_registry.async_get_registry(self.hass)
        dreg.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._hub.mac)},
            identifiers={(DOMAIN, self._hub.mac)},
            manufacturer="Hubitat",
            name="Hubitat Elevation",
        )

