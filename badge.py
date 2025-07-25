"""
Main badge class to hold all the bits and bobs
"""

import board_config as bc
from screen.st7789v import ST7789V
from screen.touch import Touchscreen
from pirda.irda import IrDA_UART
from other_hw.ws2812 import WS2812
from pirda.cir import CIR
from other_hw.external_rtc import Ext_RTC
from other_hw.accelerometer import Accelerometer
from machine import Pin, SPI
from sdcard import (
    SDCard,
)
import json
from other_hw.buzzer import Buzzer
import os
from lib.themes import Theme, builtin_themes
from lib.error_box import ErrorBox


class DC32_Badge:
    eye_pixels = (4, 5)
    front_pixels = (0, 2, 4, 5, 6)
    back_pixels = (1, 3, 7, 8)

    def __init__(self):
        prefs = self.read_preferences()
        theme_dict = prefs.get("theme")
        if theme_dict is None:
            theme = builtin_themes["engage"]
        else:
            theme = Theme(theme_dict)
        self.theme = theme
        # print(prefs)
        self.screen = ST7789V(manual_draw=True)
        # might be None, which is handled in Touchscreen initialization
        x_calibration = prefs.get("x_calibration")
        y_calibration = prefs.get("y_calibration")
        self.touch = Touchscreen(x_calibration, y_calibration)
        self.neopixels = WS2812(auto_write=True)
        self.speaker = Buzzer()
        # these can't coexist since they use the same IR hardware.
        # Set them up when they are needed with `set_ir(mode)`
        self.cir = None
        self.irda_uart = None
        self.setup_buttons()
        self.setup_sd_card()
        # TODO: these don't do anything yet
        self.ext_rtc = Ext_RTC()
        self.accelerometer = Accelerometer()
        self.animation = None

    def setup_ir(self, mode="sir"):
        if mode == "sir":
            self.cir = None
            self.irda_uart = IrDA_UART(baud_rate=19200)
        if mode == "cir":
            self.irda_uart = None
            self.cir = CIR()

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

    def setup_sd_card(self):
        spi = SPI(sck=bc.SPI_CK, miso=bc.SPI_DO, mosi=bc.SPI_DI)
        cs = Pin(bc.SD_CS, mode=Pin.OUT)
        try:
            sd = SDCard(spi=spi, cs=cs)
            os.mount(sd, "/sd")
            # print(os.listdir("sd"))
        except OSError as e:
            print(f"Error mounting SD card: {e}")
            error_box = ErrorBox(
                self,
                "Something is wrong with the SD card, and it couldn't be mounted. :( Is it inserted correctly and formatted as FAT?",
            )
            error_box.display_error()

    def set_eyes(self, rgb):
        for p in self.eye_pixels:
            self.neopixels[p] = rgb

    def set_front(self, rgb):
        for p in self.front_pixels:
            self.neopixels[p] = rgb

    def set_back(self, rgb):
        for p in self.back_pixels:
            self.neopixels[p] = rgb

    def set_pixels(self, pixel_data):
        for i, d in enumerate(pixel_data):
            # print(f"setting pixel {i} to {d}")
            self.neopixels[i] = d

    def read_preferences(self):
        prefs = {}
        try:
            with open("preferences.json", "r") as prefs_file:
                prefs = json.load(prefs_file)

        except (OSError, ValueError) as e:
            print(f"Error loading preferences: {e}")
            print("making new empty file")
            with open("preferences.json", "w") as prefs_file:
                json.dump(prefs, prefs_file)
        return prefs

    def write_preferences(self, prefs):
        with open("preferences.json", "w") as prefs_file:
            json.dump(prefs, prefs_file)
