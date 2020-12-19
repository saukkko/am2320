#!/usr/bin/env python3.8
import logging
import json
import os
from time import sleep
# this stops windows interpreter from complaining
if os.name == "posix":
    from fcntl import ioctl

# TODO
# - implement external config file from json or cmdline params
# - document all functions

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
    def __init__(self, bus: int):
        self.dev = f"/dev/i2c-{bus}"
        self.fd = os.open(self.dev, os.O_RDWR)

    def __enter__(self):
        return self

    def __exit__(self):
        if self.fd:
            os.close(self.fd)

    def close(self):
        os.close(self.fd)

    def getData(self, addr: int = sensor_addr):
        if not self.fd:
            raise IOError(f"{self.dev} is not open")
        ioctl(self.fd, 0x0703, addr)

        try:
            os.write(self.fd, bytes(0x00))
        except Exception:
            pass
        sleep(0.0010)

        os.write(self.fd, bytes([0x03, 0x00, 0x04]))
        sleep(0.0017)

        data = os.read(self.fd, 8)
        self.close()

        return list(data)


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


# return the data.
try:
    i2c = I2C(i2c_bus)
    data = i2c.getData()
    validate(data)
    humi = merge(data[2], data[3])
    temp = merge(data[4], data[5])
    if (temp & 0x8000):
        temp = -(temp & 0x7fff)

except Exception as err:
    log.error(f"Error: {err}")

else:
    print(
        f"humi: {humi/10}\ntemp: {temp/10}\nCRC: {hex(merge(data[7], data[6]))}")
