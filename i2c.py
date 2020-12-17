#!/usr/bin/env python3.8
import logging
import json
from time import sleep
from smbus2 import SMBus

logging.basicConfig(format="%(message)s")
log = logging.getLogger(__name__)

# Configure static parameters here for now.
# TODO: implement external config file from json or cmdline params

i2c_bus = 1         # i2c bus to use. default to /dev/i2c-1
sensor_addr = 0x5c  # i2c address of the device
func_code = 0x03    # always 0x03 on AM2320.
reg_len = 0x04      # AM2320 has total 4 registers for humi and temp data.
reg_start = 0x00    # start reading from zero by default


try:
    # could try `with SMBus(1) as bus:`, not sure how it works though
    bus = SMBus(i2c_bus)
except Exception as err:
    log.error(f"Error opening i2c: {err}")


def readSensor(addr=sensor_addr, start=reg_start, op=func_code, reg=reg_len):
    """
    TODO:\n
    Document this!
    """
    bus.write_byte(addr, 0, True)
    # bus.close() might be needed after every operation.
    sleep(0.0850)  # AM2320 needs 500-1000 µs of sleep after wake up

    bus.write_i2c_block_data(addr, start, [op, reg])
    sleep(0.170)  # AM2320 needs to sleep 100-200 ms before reading the registers

    data = bus.read_i2c_block_data(addr, start, reg)
    bus.close()

    # TODO:
    # Implement (or find) crc16 function to verify the data.
    # do not return the value unless crc16 passes.
    # if crc16 does not pass we need to wait xxx ms to read again.

    # C Code below:
    """
    unsigned short crc16(unsigned char *ptr, unsigned char len)
    {
        unsigned short crc = 0xFFFF;
        unsigned char i;
        while (len--)
        {
            crc ^= *ptr++;
            for (i = 0; i < 8; i++)
            {
                if (crc & 0x01)
                {
                    crc >>= 1;
                    crc ^= 0xA001;
                }
                else
                {
                    crc >>= 1;
                }
            }
        }
        return crc;
    }
    """

    # return the data as hex list for now
    return data
