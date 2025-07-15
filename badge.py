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
)  # consider importing this late or actually including a copy of the micropython lib files
import json
from other_hw.buzzer import Buzzer
import os
from lib.themes import Theme, builtin_themes

# from lib.common import int32_to_bytes


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
        self.screen = ST7789V()
        # might be None, which is handled in Touchscreen initialization
        x_calibration = prefs.get("x_calibration")
        y_calibration = prefs.get("y_calibration")
        self.touch = Touchscreen(x_calibration, y_calibration)
        self.neopixels = WS2812(auto_write=True)
        self.speaker = Buzzer()
        # self.cir = CIR()
        # self.irda_uart = IrDA_UART(baud_rate=19200)
        self.cir = None
        self.irda_uart = None
        self.setup_buttons()
        self.setup_sd_card()
        # TODO: these don't do anything yet
        self.ext_rtc = Ext_RTC()
        self.accelerometer = Accelerometer()
        self.animation = None
        # # TODO: if this is to become a real feature, persist it in a json file
        # self.screenshot_counter = 0

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
            self.screen.fill(self.theme.bg1)
            self.screen.text_in_box(
                "Note: Something is wrong with the SD card, and it couldn't be mounted. :( Is it inserted correctly and formatted as FAT?",
                10,
                10,
                self.theme.fg1,
                self.theme.bg2,
                text_width=300,
                fill=True,
            )
            self.screen.frame_buf.text("Press A to dismiss", 10, 200, self.theme.fg2)
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
        return prefs

    def write_preferences(self, prefs):
        with open("preferences.json", "w") as prefs_file:
            json.dump(prefs, prefs_file)

    ## TODO: under construction
    ## currently the image this saves is upside down and has incorrect colors
    ## I understand why it's upside down but not why the colors are wrong
    # def save_screenshot(self, filename):'

    #     """
    #     https://github.com/kentoj/python-fundamentals

    #     A module for dealing with BMP bitmap image files.
    #     MIT License

    #     Copyright (c) 2016 Kent Johnson

    #     Permission is hereby granted, free of charge, to any person obtaining a copy
    #     of this software and associated documentation files (the "Software"), to deal
    #     in the Software without restriction, including without limitation the rights
    #     to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    #     copies of the Software, and to permit persons to whom the Software is
    #     furnished to do so, subject to the following conditions:

    #     The above copyright notice and this permission notice shall be included in all
    #     copies or substantial portions of the Software.

    #     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    #     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    #     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    #     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    #     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    #     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    #     SOFTWARE.
    #     """
    #     old_dir = os.getcwd()
    #     os.chdir("/sd")
    #     with open(filename, "wb") as bmp:
    #         # BMP Header
    #         bmp.write(b"BM")

    #         size_bookmark = (
    #             bmp.tell()
    #         )  # The next four bytes hold the filesize as a 32-bit
    #         bmp.write(
    #             b"\x00\x00\x00\x00"
    #         )  # little-endian integer. Zero placeholder for now.

    #         bmp.write(b"\x00\x00")  # Unused 16-bit integer - should be zero
    #         bmp.write(b"\x00\x00")  # Unused 16-bit integer - should be zero

    #         pixel_offset_bookmark = (
    #             bmp.tell()
    #         )  # The next four bytes hold the integer offset
    #         bmp.write(
    #             b"\x00\x00\x00\x00"
    #         )  # to the pixel data. Zero placeholder for now.

    #         # Image header
    #         bmp.write(b"\x28\x00\x00\x00")  # Image header size in bytes - 40 decimal
    #         bmp.write(int32_to_bytes(bc.SCREEN_WIDTH))  # Image width in pixels
    #         bmp.write(int32_to_bytes(bc.SCREEN_HEIGHT))  # Image height in pixels
    #         bmp.write(b"\x01\x00")  # Number of image planes
    #         bmp.write(b"\x10\x00")  # Bits per pixel 16 for rgb565
    #         bmp.write(b"\x00\x00\x00\x00")  # No compression
    #         bmp.write(b"\x00\x00\x00\x00")  # Zero for uncompressed images
    #         bmp.write(b"\x00\x00\x00\x00")  # Unused: pixels per meter
    #         bmp.write(b"\x00\x00\x00\x00")  # Unused: pixels per meter
    #         bmp.write(b"\x00\x00\x00\x00")  # Use whole color table
    #         bmp.write(b"\x00\x00\x00\x00")  # All colors are important

    #         # # Color palette - a linear grayscale
    #         # for c in range(256):
    #         #     bmp.write(bytes((c, c, c, 0)))

    #         # Pixel data
    #         pixel_data_bookmark = bmp.tell()
    #         # dump framebuf here
    #         # tried offsetting by a byte, doing it little and big endian, got different but still incorrect colors
    #         bmp.write(self.screen.frame_buf)

    #         # End of file
    #         eof_bookmark = bmp.tell()

    #         # Fill in file size placeholder
    #         bmp.seek(size_bookmark)
    #         bmp.write(int32_to_bytes(eof_bookmark))

    #         # Fill in pixel
    #         bmp.seek(pixel_offset_bookmark)
    #         bmp.write(int32_to_bytes(pixel_data_bookmark))
    #     os.chdir(old_dir)
    #     print(f"Saved screenshot {filename}")

    # def screenshot_cb(self, arg):
    #     self.save_screenshot(f"screenshot_{self.screenshot_counter}.bmp")
    #     self.screenshot_counter += 1
