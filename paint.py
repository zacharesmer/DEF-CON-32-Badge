"""
A program where you can draw and also send your drawing to another person
"""

import time
from machine import Pin, Timer
import random
from array import array
import lib.common as common
from lib.animations import BlinkRed
from badge import DC32_Badge

import asyncio
import gc

# import micropython
# micropython.alloc_emergency_exception_buf(100)

# TODO: use less memory If I add color selectors on the sides to take up enough space
# that the drawing area is only 240 * 255, I can take up half as much space storing the history.


class Program:
    def __init__(self, badge=None):
        if badge is None:
            badge = DC32_Badge()
        self.badge = badge
        self.tft = badge.screen
        self.touch = badge.touch
        self.canvas_x = 319
        self.canvas_y = 239
        print(f"Available: {gc.mem_free()}")
        # size = min(20_000, round(gc.mem_free() / 50))
        size = 5_000
        print(f"using {size}")
        self.history = PaintHistory(size, self.canvas_x, self.canvas_y)
        self.color, self.bg_color = self.random_colors()
        self.version = 0

    def random_colors(self):
        fgh = random.random()
        bgh = random.random()
        # make sure there's decent contrast
        bgv = 1
        if abs(fgh - bgh) < 0.3:
            bgv = 0.5
        return common.Color(fgh, 1, 1, "paint"), common.Color(bgh, 1, bgv, "paint")

    def setup_buttons(self):
        self.badge.start_button.irq(self.clear_screen, trigger=Pin.IRQ_FALLING)
        self.badge.a_button.irq(self.go_forward, trigger=Pin.IRQ_FALLING)
        self.badge.b_button.irq(self.go_back, trigger=Pin.IRQ_FALLING)
        self.badge.right_button.irq(self.send_drawing, trigger=Pin.IRQ_FALLING)
        self.badge.left_button.irq(self.receive_drawing, trigger=Pin.IRQ_FALLING)

    def clear_screen(self, *args):
        self.color, self.bg_color = self.random_colors()
        # TODO make some fun effects for coloring in the new background color (random lines, dots, etc.)
        self.tft.fill(self.bg_color.c565)
        self.badge.set_back(self.bg_color)
        self.badge.set_front(self.color)
        self.history.clear()

    def go_back(self, *args):
        # print(args)
        while args[0].value() == 0:
            if self.history.index > 0:
                # erase the pixel
                self.tft.fill_circle(
                    self.history.x(),
                    self.history.y(),
                    3,
                    self.bg_color.c565,
                )
                self.history.index -= 1
                time.sleep_ms(self.history.sleep_time)

    def go_back_async(self, *args):
        # if the button has stopped being pressed, stop going back
        if args[0].value() != 0:
            return
        button = args[0]
        if self.history.index > 0:
            # erase the pixel
            self.tft.fill_circle(
                self.history.x(),
                self.history.y(),
                3,
                self.bg_color.c565,
            )
            self.history.index -= 1
            Timer(
                mode=Timer.ONE_SHOT,
                period=self.history.sleep_time,
                callback=lambda *args: self.go_back_async(button),
            )

    def go_forward(self, *args):
        while args[0].value() == 0:
            if self.history.index < self.history.latest_valid_index:
                self.history.index += 1
                self.tft.fill_circle(
                    self.history.x(), self.history.y(), 3, self.color.c565
                )
                time.sleep_ms(self.history.sleep_time)

    def go_forward_async(self, *args):
        # if the button has stopped being pressed, stop going forward
        if args[0].value() != 0:
            return
        button = args[0]
        if self.history.index < self.history.latest_valid_index:
            self.history.index += 1
            self.tft.fill_circle(self.history.x(), self.history.y(), 3, self.color.c565)
            Timer(
                mode=Timer.ONE_SHOT,
                period=self.history.sleep_time,
                callback=lambda *args: self.go_forward_async(button),
            )

    def send_drawing(self, *args):
        # message header: version, data size in words, color, 5 words reserved for future use
        self.badge.irda_uart.reset_machines()
        anim = BlinkRed(brightness=100, delay=30)
        self.badge.irda_uart.send_word(self.version)
        print(f"Sending data size: {self.history.index}")
        send_start = time.time_ns()
        self.badge.irda_uart.send_word(self.history.index)
        asyncio.sleep_ms(self.history.sleep_time)
        self.badge.irda_uart.send_word(self.color.c565)
        # 5 words of nothing in case theres something to add in a future version
        for _ in range(5):
            self.badge.irda_uart.send_word(0)
        asyncio.sleep_ms(self.history.sleep_time)
        for i in range(1, self.history.index + 1):
            self.badge.set_eyes(anim.next())
            self.badge.irda_uart.send_word(self.history.get_point(i))

        print("sent")
        print(f"took {(time.time_ns() - send_start)/10**6} ms")
        self.badge.set_eyes(self.color)
        # print("why so slow??")

    def receive_drawing(self, *args):
        print("receiving...")
        anim = BlinkRed(brightness=100, delay=400)
        self.badge.set_eyes(anim.next())
        self.badge.irda_uart.reset_machines()
        version = None
        size = None
        other_color = None
        rxed = 0

        # message header size: 8 words
        # so far the format is version, message data size in words, color, 5 words of nothing

        # TODO: actually clear out the fifo, seems like something is wrong and causing me to get 0xFF_FF_FF_FF
        while (version is None or version == 0xFF_FF_FF_FF) and args[0].value() == 0:
            version = self.badge.irda_uart.receive_word()
            self.badge.set_eyes(anim.next())
        if args[0].value() == 1:
            print("No version :(")
            self.badge.set_front(self.color)
            return

        while (size is None) and args[0].value() == 0:
            size = self.badge.irda_uart.receive_word()
            self.badge.set_eyes(anim.next())
        if args[0].value() == 1:
            print("No size :(")
            self.badge.set_front(self.color)
            return

        print(f"Message data size {size:032b}")
        while other_color is None and args[0].value() == 0:
            other_color = self.badge.irda_uart.receive_word()
            self.badge.set_eyes(anim.next())
        if other_color is None:
            print("No color :(")
            self.badge.set_front(self.color)
            return

        # ignore the next 5 words because I may want to use them for something in the future
        for _ in range(5):
            ignore = None
            while ignore is None and args[0].value() == 0:
                ignore = self.badge.irda_uart.receive_word()
                self.badge.set_eyes(anim.next())
            # if we stopped holding down the button bail out
            if args[0].value() == 1:
                self.badge.set_front(self.color)
                return

        while args[0].value() == 0 and rxed < size:
            self.badge.set_eyes(anim.next())
            val = None
            while val is None and args[0].value() == 0:
                self.badge.set_eyes(anim.next())
                val = self.badge.irda_uart.receive_word()
                # if val is None:
                # print("wait")
            if val is None:
                break
            # print(f"{val:032b}")
            if self.history.add_point(val):
                self.tft.fill_circle(self.history.x(), self.history.y(), 3, other_color)
            rxed += 1
            # print(f"{history.x()}, {history.y()}")
        self.badge.set_front(self.color)

    async def run(self):
        self.badge.setup_ir(mode="sir")
        self.setup_buttons()
        self.clear_screen()
        prev_x, prev_y = (0, 0)
        self.is_running = True
        while self.is_running:
            await asyncio.sleep(0)
            # if (start_button.value() == 0):
            #     clear_screen(start_button)
            # if (a_button.value() == 0):
            #     go_forward_async(a_button)
            # if (b_button.value() == 0):
            #     go_back_async(b_button)
            # if right_button.value() == 0:
            #     send_drawing(right_button)
            # if left_button.value() == 0:
            #     receive_drawing(left_button)

            t = self.touch.get_one_touch_in_pixels(verbose=False)
            if t is not None:
                x, y = t
                # ignore any touches that are really close to the last recorded touch
                if (x - prev_x) ** 2 + (y - prev_y) ** 2 > 4:
                    prev_x, prev_y = t
                    if self.history.add_x_y(x, y):
                        self.tft.fill_circle(x, y, 3, self.color.c565)
        # teardown
        del self.history.points
        del self.history
        self.badge.start_button.irq(None)
        self.badge.a_button.irq(None)
        self.badge.b_button.irq(None)
        self.badge.right_button.irq(None)
        self.badge.left_button.irq(None)
        self.badge.neopixels.fill((0, 0, 0))
        self.badge.irda_uart = None

    async def exit(self):
        self.is_running = False


class PaintHistory:
    # TODO: make some kind of frame around the drawing area so it's only 255 x 240 so I can hold more dots in the history?
    def __init__(self, history_size, x, y):
        self.canvas_x = x
        self.canvas_y = y
        # index is the most recently written index of the history array
        self.index = 0
        # this is the latest valid index to fast forward to and write to
        # if we've undone, it will not match the current index
        self.latest_valid_index = 0

        self.max_size = history_size - 1
        self.sleep_time = 1

        self.points = array("i", [0 for _ in range(history_size)])

    def clear(self):
        self.index = 0
        self.latest_valid_index = 0

    def x(self):
        return (self.points[self.index] >> 16) & 0x00_00_FF_FF

    def y(self):
        return self.points[self.index] & 0x00_00_FF_FF

    def add_x_y(self, x, y):
        return self.add_point((x << 16) | (y & 0x00_00_FF_FF))

    def add_point(self, p):
        # make sure it's actually a valid coordinate before saving it
        if (
            p >> 16
        ) & 0x00_00_FF_FF < self.canvas_x and p & 0x00_00_FF_FF < self.canvas_y:
            if self.index >= self.max_size:
                # history.index = 0
                print("outta space")
                return False
            self.index += 1
            self.points[self.index] = p
            self.latest_valid_index = self.index
            return True
        return False

    def get_point(self, index):
        return self.points[index]
