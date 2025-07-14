"""
TODO: actually make this do stuff

RTC
PCF8563T/5,518
SOIC-8

"""

from machine import SoftI2C, Pin
import board_config as bc


class Ext_RTC:
    def __init__(self):
        self.i2c = SoftI2C(
            scl=Pin(bc.I2C_SCL),
            sda=Pin(
                bc.I2C_SDA,
            ),
        )
        self.addr_read = 0xA3
        self.add_write = 0xA2
