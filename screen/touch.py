"""
Very small driver for the touch controller
"""

import board_config
from machine import Pin, SoftI2C


class Touchscreen:

    def __init__(
        self,
        # not sure if these will work for every badge
        x_calibration=None,
        y_calibration=None,
    ):
        self.x_cal = (-0.09056061, 356.5392) if x_calibration is None else x_calibration
        self.y_cal = (-0.06559808, 253.8693) if y_calibration is None else y_calibration
        self.i2c = SoftI2C(
            scl=Pin(board_config.I2C_SCL),
            sda=Pin(
                board_config.I2C_SDA,
            ),
        )
        self.x = self.y = self.z = 0
        self.addr = 0x48
        self.z_thr = 40

    def _read(self, cmd):
        buff = self.i2c.readfrom_mem(self.addr, cmd, 2)
        v = (buff[0] << 4) | (buff[1] >> 4)
        return v

    def update(self):
        self.z = self._read(0xE0)
        if self.z > self.z_thr:
            self.x = self._read(0xC0)
            self.y = self._read(0xD0)
            # print(f"touch x={self.x} y={self.y} z={self.z}")
        else:
            self.x = self.y = -1

    def get_one_touch(self):
        self.update()
        if (self.x != -1 and self.x < 4090) or (self.x != -1 and self.y < 4090):
            return (self.x, self.y)
        return None

    def get_one_touch_in_pixels(self, verbose=False):
        # print("getting a touch!")
        self.update()
        if (self.x != -1 and self.x < 4090) or (self.x != -1 and self.y < 4090):
            if verbose:
                print(f"{self.pixel_x()}, {self.pixel_y()}")
            return (self.pixel_x(), self.pixel_y())
        else:
            return None

    def pixel_x(self):
        return round(self.x_cal[0] * self.x + self.x_cal[1])

    def pixel_y(self):
        return round(self.y_cal[0] * self.y + self.y_cal[1])

    def set_calibration(self, x_cal, y_cal):
        self.x_cal = x_cal
        self.y_cal = y_cal
