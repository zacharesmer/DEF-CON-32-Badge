import board_config as bc
from screen.st7789v import ST7789V
from screen.touch import Touchscreen
from pirda.irda import IrDA_UART
from other_hw.ws2812 import WS2812
from pirda.cir import CIR
from machine import Pin, SPI
from sdcard import (
    SDCard,
)  # consider importing this late or actually including a copy of the micropython lib files
import json
from other_hw.buzzer import Buzzer
import os
import asyncio


class DC32_Badge:
    eye_pixels = (4, 5)
    front_pixels = (0, 2, 4, 5, 6)
    back_pixels = (1, 3, 7, 8)

    def __init__(self):
        prefs = self.read_preferences()
        # print(prefs)
        self.screen = ST7789V()
        x_calibration = prefs.get("x_calibration")
        y_calibration = prefs.get("y_calibration")
        self.touch = Touchscreen(x_calibration, y_calibration)
        self.irda_uart = IrDA_UART(baud_rate=19200)
        self.neopixels = WS2812(auto_write=True)
        self.speaker = Buzzer()
        self.cir = CIR()
        self.setup_buttons()
        self.setup_sd_card()

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
            print(e)
            self.screen.fill(0x00_00)
            self.screen.frame_buf.text("Note:", 10, 10, 0xFF_FF)
            self.screen.frame_buf.text(
                "Something is wrong with the SD card",
                10,
                40,
                0xFF_FF,
            )
            self.screen.frame_buf.text(
                "and it couldn't be mounted :(",
                10,
                55,
                0xFF_FF,
            )
            self.screen.frame_buf.text(
                "Is it inserted correctly and",
                10,
                80,
                0xFF_FF,
            )
            self.screen.frame_buf.text("formatted as FAT?", 10, 95, 0xFF_FF)
            self.screen.frame_buf.text("Press A to dismiss", 10, 120, 0xFF_FF)
            while self.a_button.value() != 0:
                pass

    def set_eyes(self, rgb):
        for p in self.eye_pixels:
            self.neopixels[p] = rgb

    def set_front(self, rgb):
        for p in self.front_pixels:
            self.neopixels[p] = rgb

    def set_back(self, rgb):
        for p in self.back_pixels:
            self.neopixels[p] = rgb

    async def set_touch_calibration(self, prefs):
        print("hiiiii")
        # if no calibration is set, run the calibration program

    def read_preferences(self):
        prefs = {}
        try:
            with open("preferences.json", "r") as prefs_file:
                try:
                    prefs = json.load(prefs_file)
                except ValueError as ve:
                    # TODO: this means the JSON format is borked, consider copying a default config file
                    print(ve)
        except OSError as e:
            print(e)
            print("couldn't open file, returning empty preferences")
        return prefs

    def write_preferences(self, prefs):
        with open("preferences.json", "w") as prefs_file:
            json.dump(prefs, prefs_file)
