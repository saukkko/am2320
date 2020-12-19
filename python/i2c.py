#!/usr/bin/env python3.8
import logging
import json
import os
from time import sleep

# TODO
# - implement external config file from json or cmdline params
# - replace smbus2 with direct reads from /dev/i2c by os module (https://docs.python.org/3/library/os.html#module-os)
# - document all functions
# - call the functions and return the data back

logging.basicConfig(format="%(message)s")
log = logging.getLogger(__name__)

# Configure static parameters here for now.

i2c_bus = 1         # i2c bus to use. default to /dev/i2c-1
sensor_addr = 0x5c  # i2c address of the device
func_code = 0x03    # always 0x03 on AM2320.
reg_len = 0x04      # AM2320 has total 4 registers for humi and temp data.
reg_start = 0x00    # start reading from zero by default


# test data
test_data = [
    0x03, 0x04,     # func + number of registers
    0x02, 0x14,     # 532 = 53.2 RH %
    0x01, 0x05,     # 261 = 26.1 °C
    0x71, 0xC7      # checksum
]


class I2C(object):
    """
    docstring
    """

    def __init__(self, bus: int):
        dev = f"/dev/i2c-{bus}"

        try:
            if os.name != "posix":
                raise Exception(
                    "Sorry, only posix (unix-like) file descriptors are supported")
            if not os.path.exists(dev):
                raise Exception("dev does not exist")
        except Exception as err:
            log.error(f"Error opening device: {err}")
        else:
            fd = os.open(dev, os.O_RDWR)
        return None

    def write(self):
        pass


def readSensor(addr=sensor_addr, start=reg_start, op=func_code, reg=reg_len):
    """
    Document this!
    """
    bus.write_byte(addr, 0, True)
    # bus.close() might be needed after every operation.
    sleep(0.00085)  # AM2320 needs 800-3000 µs of sleep after wake up

    bus.write_i2c_block_data(addr, start, [op, reg])
    # AM2320 needs to sleep at least 1.5 ms before reading the registers
    sleep(0.00170)

    data = bus.read_i2c_block_data(addr, start, reg)
    bus.close()

    return data


def validate(data: list):
    """
    Document this!
    """
    try:
        # actually data[1] should be number of registers read, so its not always 0x04
        if data[0] != 0x03 and data[1] != 0x04:
            raise Exception("ACK mismatch")
        crc = merge(data[7], data[6])
        if crc16(data[0:6]) != crc:
            raise Exception("CRC mismatch")
    except Exception as err:
        log.warning(f"Warning: {err}")
    return data


def crc16(data: list):
    crc = 0xFFFF

    for i in data:
        crc = crc ^ i
        for bit in range(8):
            if (crc & 0x0001):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


def merge(a: int, b: int, numbits: int = 8):
    return (a << numbits) | b


# open i2c
bus = I2C(i2c_bus)

# return the data.
try:
    data = validate(test_data)
    humi = merge(data[2], data[3])
    temp = merge(data[4], data[5])
    if (temp & 0x8000):
        temp = -(temp & 0x7fff)
except Exception as err:
    log.error(err)
else:
    pass
finally:
    print(f"humi: {humi/10}\ntemp: {temp/10}")
