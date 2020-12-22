#!/usr/bin/env python3.8
import os
from time import sleep
# this stops windows interpreter from complaining
if os.name == "posix":
    from fcntl import ioctl

# TODO
# - implement external config file from json or cmdline params
# - document all functions


# Configure static parameters here for now.

i2c_bus = 1         # i2c bus to use. default to /dev/i2c-1
sensor_addr = 0x5c  # i2c address of the device
func_code = 0x03    # always 0x03 on AM2320.
reg_len = 0x04      # AM2320 has total 4 registers for humi and temp data.
reg_start = 0x00    # start reading from zero by default


class I2C(object):
    def __init__(self, bus: int = i2c_bus):
        self.dev = f"/dev/i2c-{bus}"
        self.fd = os.open(self.dev, os.O_RDWR)
        self.write_cmd = bytes([func_code, reg_start, reg_len])

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

        os.write(self.fd, self.write_cmd)
        sleep(0.0017)

        data = os.read(self.fd, 8)
        self.close()

        valid_data = self.__validate(data)

        humi = self.__merge(valid_data[2], valid_data[3])
        temp = self.__merge(valid_data[4], valid_data[5])

        if (temp & 0x8000):
            temp = -(temp & 0x7fff)

        return dict({
            f"humidity": humi/10,
            f"temperature": temp/10
        })

    def __validate(self, data: bytes):
        """
        Document this!
        """

        if data[0] != self.write_cmd[0] and data[1] != self.write_cmd[2]:
            raise Exception("ACK mismatch")
        crc = self.__merge(data[7], data[6])
        if self.__crc16(data[0:6]) != crc:
            raise Exception("CRC mismatch")
        return data

    @staticmethod
    def __crc16(data: bytes):
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

    @staticmethod
    def __merge(a: int, b: int, numbits: int = 8):
        return (a << numbits) | b
