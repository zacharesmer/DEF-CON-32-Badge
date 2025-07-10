import board_config as bc
from screen.st7789v import ST7789V
from screen.touch import Touchscreen
from pirda.irda import IrDA_UART
from ws2812 import WS2812
from machine import Pin
import json
from buzzer import Buzzer
import os


class DC32_Badge:
    eye_pixels = (4, 5)
    front_pixels = (0, 2, 4, 5, 6)
    back_pixels = (1, 3, 7, 8)

    def __init__(self):
        prefs = self.read_preferences()
        # print(prefs)
        self.screen = ST7789V()
        # TODO if no calibration is set, run the calibration program
        self.touch = Touchscreen(
            x_calibration=prefs.get("x_calibration"),
            y_calibration=prefs.get("y_calibration"),
        )
        self.irda_uart = IrDA_UART(baud_rate=19200)
        self.neopixels = WS2812(auto_write=True)
        self.speaker = Buzzer()
        self.setup_buttons()

    def setup_buttons(self):
        self.up_button = Pin(bc.UP_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self.down_button = Pin(bc.DOWN_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self.right_button = Pin(bc.RIGHT_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self.left_button = Pin(bc.LEFT_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)

        self.a_button = Pin(bc.A_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b_button = Pin(bc.B_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)

        self.start_button = Pin(bc.START_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self.select_button = Pin(bc.SELECT_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)

        self.fn_button = Pin(bc.FN_BUTTON, Pin.IN, pull=Pin.PULL_UP)

    def set_eyes(self, rgb):
        for p in self.eye_pixels:
            self.neopixels[p] = rgb

    def set_front(self, rgb):
        for p in self.front_pixels:
            self.neopixels[p] = rgb

    def set_back(self, rgb):
        for p in self.back_pixels:
            self.neopixels[p] = rgb

    def read_preferences(self):
        prefs = {}
        with open("preferences.json", "r") as prefs_file:
            try:
                prefs = json.load(prefs_file)
            except ValueError as ve:
                # TODO: this means the JSON format is borked, consider copying a default config file
                print(ve)
        return prefs

    def write_preferences(self, prefs):
        with open("preferences.json", "w") as prefs_file:
            json.dump(prefs, prefs_file)
