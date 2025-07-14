"""
TODO: actually make this do stuff

3-Axis Accelerometer
LIS3DHTR
LGA-16

"""


from machine import SoftI2C, Pin
import board_config as bc


class Accelerometer:
    def __init__(self):
        self.i2c = SoftI2C(
            scl=Pin(bc.I2C_SCL),
            sda=Pin(
                bc.I2C_SDA,
            ),
        )
        self.addr_high = 0x19
        self.add_low = 0x18

