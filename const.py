"""Constants for the EnOcean integration."""

DOMAIN = "my_enocean"

CONF_ENTRY_ID = "entry_id"
CONF_SERIAL_PORT = "serial_port"
CONF_IDENTIFIERS = "identifiers"
CONF_MANUFACTURER = "manufacturer"
CONF_MODEL = "model"
CONF_VIA_DEVICE = "via_device"
CONF_NO_OF_CHANNELS = "no_of_channels"
CONF_OPTION = "option"
CONF_LOADED = "loaded"

DATA_BASE = "data_base"
DATA_CONFIG = "data_config"
DATA_DEVICES = "data_devices"
DATA_DISPATCHERS = "data_dispatchers"
DATA_DONGLE = "data_dongle"
DATA_PLATFORM = "data_platform"

DEFAULT_CONF_HUB_SERIAL_PORT = "/dev/ttyS3"
DEFAULT_CONF_HUB_MANUFACTURER = "element14"
DEFAULT_CONF_HUB_MODEL = "TCM 310"
DEFAULT_DATABASE_NAME = "enocean.sqlite"

#DEVICE_MANUFACTURER_NODON = "NodOn"
#DEVICE_MANUFACTURER_ELTAKO = "Eltako"
#DEVICE_MANUFACTURERS = [DEVICE_MANUFACTURER_ELTAKO, DEVICE_MANUFACTURER_NODON]
#
#DEVICE_MODEL_NODON_SIN_2_1_01 = "SIN-2-1-01"
#DEVICE_MODEL_ELTAKO_FSR61NP = "FSR61NP"
#DEVICE_MODELS = [DEVICE_MODEL_ELTAKO_FSR61NP, DEVICE_MODEL_NODON_SIN_2_1_01]

ENOCEAN_TRANSCEIVER = "EnOcean Transceiver"
ENOCEAN_SWITCH = "EnOcean Switch"

#OPTION_NONE = ""
#OPTION_ADD_SWITCH = "add_switch"
#OPTION_TEACH_IN = "Teach-In"
#OPTION_LIST = [OPTION_NONE,OPTION_ADD_SWITCH,OPTION_TEACH_IN]

RETURN_DB_NEW = "return_db_new"
RETURN_DB_EXISTING = "return_db_existing"

SERVICE_TEACH_IN = "service_teach_in"
SERVICE_ADD_SWITCH = "service_add_switch"
SERVICE_REMOVE_DEVICE = "service_remove_device"

SIGNAL_RECEIVE_PACKET = "enocean.receive_packet"
SIGNAL_SEND_PACKET = "enocean.send_packet"
SIGNAL_TEACH_IN = "enocean.teach_in"
SIGNAL_ADD_ENTITIES = "enocean.add_entities"


DEVICES_EEP = {
    "NodOn_SIN-2-1-01": ["TeachIn_UTE", "D2-01-00"],
    "NodOn_SIN-2-2-01": ["TeachIn_UTE", "D2-01-00"],
    "Eltako_FSR61NP": ["TeachIn_4BS", "A5-38-08"],
    "FLEXtron_300610": ["TeachIn_4BS", "A5-38-08"],
    }
