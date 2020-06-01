"""Helper functions to interact with database storing network data persistently."""
import logging
import asyncio
import os
import sqlite3

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
    CONF_VIA_DEVICE,
    CONF_NO_OF_CHANNELS,
)
from .const import (
    DEFAULT_DATABASE_NAME,
)
from .const import (
    RETURN_DB_NEW,
    RETURN_DB_EXISTING,
)

_LOGGER = logging.getLogger(__name__)


def database_init(hass, database_name=DEFAULT_DATABASE_NAME):
    db_file = os.path.join(hass.config.config_dir, database_name)
    if os.path.isfile(db_file):
        return RETURN_DB_EXISTING
    else:
        # Create and connect to database
        db_con = sqlite3.connect(db_file)
        # Create a cursor
        db_cur = db_con.cursor()
        # Create tables
        db_cur.execute(f'''CREATE TABLE devices (
            {CONF_ID} TEXT,
            {CONF_MANUFACTURER} TEXT,
            {CONF_MODEL} TEXT,
            {ATTR_DEVICE_CLASS} TEXT
            )''')
        # Commit changes to database
        db_con.commit()
        # Close connection
        db_con.close()
    
        return RETURN_DB_NEW


def database_add_device(db_file, dev_dict):
    # Create and connect to database
    db_con = sqlite3.connect(db_file)
    # Create a cursor
    db_cur = db_con.cursor()

    db_cur.execute(
        'INSERT INTO devices VALUES ("{}","{}","{}","{}")'.format(
            dev_dict[CONF_ID],
            dev_dict[CONF_MANUFACTURER],
            dev_dict[CONF_MODEL],
            dev_dict[ATTR_DEVICE_CLASS]
        )
    )
    
    # Commit changes to database
    db_con.commit()
    # Close connection
    db_con.close()


def database_remove_device(db_file, dev_id):
    # Create and connect to database
    db_con = sqlite3.connect(db_file)
    # Create a cursor
    db_cur = db_con.cursor()

    db_cur.execute(f"DELETE FROM devices WHERE {CONF_ID} LIKE '{dev_id}'")
    
    # Commit changes to database
    db_con.commit()
    # Close connection
    db_con.close()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        #d[col[0]] = row[idx]
        if (
            (col[0]==CONF_ID) or 
            (col[0]==ATTR_DEVICE_CLASS) or 
            (col[0]==CONF_VIA_DEVICE)
        ):
            d[col[0]] = eval(row[idx])
        else:
            d[col[0]] = row[idx]

    return d


def database_get_device(db_file, dev_id):
    # Create and connect to database
    db_con = sqlite3.connect(db_file)
    # Create row factory to access search results as dictionary
    db_con.row_factory = dict_factory
    # Create a cursor
    db_cur = db_con.cursor()

    dev_dict = {}
    if dev_id==[0xFF,0xFF,0xFF,0xFF]:
        _LOGGER.debug(f"fetchall")
        db_cur.execute(f"SELECT * FROM devices")
        dev_dict = db_cur.fetchall()
    else:
        db_cur.execute(f"SELECT * FROM devices WHERE {CONF_ID} LIKE '{dev_id}'")
        dev_dict = db_cur.fetchone()

    # Commit changes to database
    db_con.commit()
    # Close connection
    db_con.close()

    return dev_dict


def database_update_hub(db_file, dev_dict):
    # Create and connect to database
    db_con = sqlite3.connect(db_file)
    # Create row factory to access search results as dictionary
    db_con.row_factory = dict_factory
    # Create a cursor
    db_cur = db_con.cursor()

    db_cur.execute(f"UPDATE devices SET {CONF_ID}='{dev_dict[CONF_ID]}' WHERE {ATTR_DEVICE_CLASS} LIKE '%{CONF_BASE}%'")
    db_cur.execute(f"UPDATE devices SET {CONF_MANUFACTURER}='{dev_dict[CONF_MANUFACTURER]}' WHERE {ATTR_DEVICE_CLASS} LIKE '%{CONF_BASE}%'")
    db_cur.execute(f"UPDATE devices SET {CONF_MODEL}='{dev_dict[CONF_MODEL]}' WHERE {ATTR_DEVICE_CLASS} LIKE '%{CONF_BASE}%'")

    # Commit changes to database
    db_con.commit()
    # Close connection
    db_con.close()

    return True

