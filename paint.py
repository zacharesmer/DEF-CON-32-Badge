"""
A program where you can draw and also send your drawing to another person
"""

import board_config
import time
from machine import Pin, Timer
import random
from array import array
import lib
from animation_lib import BlinkRed
from badge import DC32_Badge

import asyncio

# import micropython
# micropython.alloc_emergency_exception_buf(100)

# TODO: this uses way too much memory. If I add color selectors on the sides to take up enough space
# that the drawing area is only 240 * 255, I can take up half as much space storing the history,
# which I think would fix it. Also if I can figure out why the memory isn't getting freed that could help too...


class Program:
    def __init__(self, badge=None):
        if badge is None:
            badge = DC32_Badge()
        self.badge = badge
        self.irda_uart = badge.irda_uart
        self.tft = badge.screen
        self.touch = badge.touch
        self.history = PaintHistory()

        self.color, self.bg_color = self.random_colors()

    def random_colors(self):
        fgh = random.random()
        bgh = random.random()
        # make sure there's decent contrast
        bgv = 1
        if abs(fgh - bgh) < 0.3:
            bgv = 0.5
        return lib.Color(fgh, 1, 1, "paint"), lib.Color(bgh, 1, bgv, "paint")

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
        print(args)
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
        self.irda_uart.reset_machines()
        anim = BlinkRed(brightness=100, delay=30)
        print(f"Sending size: {self.history.index}")
        send_start = time.time_ns()
        self.irda_uart.send_word(self.history.index)
        asyncio.sleep_ms(self.history.sleep_time)
        # time.sleep_ms(history.sleep_time)
        self.irda_uart.send_word(self.color.c565)
        asyncio.sleep_ms(self.history.sleep_time)
        # time.sleep_ms(history.sleep_time)
        for i in range(1, self.history.index + 1):
            self.badge.set_eyes(anim.next())
            # p_x = history.x[i]
            # p_y = history.y[i]
            # print(f"{history.get_point(i):032b}")
            self.irda_uart.send_word(self.history.get_point(i))

        print("sent")
        print(f"took {(time.time_ns() - send_start)/10**6} ms")
        self.badge.set_eyes(self.color)
        # print("why so slow??")

    def receive_drawing(self, *args):
        print("receiving...")
        anim = BlinkRed(brightness=100, delay=400)
        self.badge.set_eyes(anim.next())
        self.irda_uart.reset_machines()
        size = None
        other_color = None
        rxed = 0
        # TODO: actually clear out the fifo, seems like something is wrong idk
        while (size is None or size == 0xFF_FF_FF_FF) and args[0].value() == 0:
            size = self.irda_uart.receive_word()
            self.badge.set_eyes(anim.next())

        if size is None or size == 0xFF_FF_FF_FF:
            print("No size :(")
            self.badge.set_front(self.color)
            return
        print(f"{size:032b}")
        while other_color is None and args[0].value() == 0:
            other_color = self.irda_uart.receive_word()
            if other_color is not None:
                print(other_color)
            # asyncio.sleep(0)
            self.badge.set_eyes(anim.next())

        if other_color is None:
            print("No color :(")
            self.badge.set_front(self.color)
            return
        while args[0].value() == 0 and rxed < size:
            self.badge.set_eyes(anim.next())
            val = None
            while val is None and args[0].value() == 0:
                self.badge.set_eyes(anim.next())
                val = self.irda_uart.receive_word()
                # if val is None:
                # print("wait")
            if val is None:
                break
            # print(f"{val:032b}")
            self.history.add_point(val)
            rxed += 1
            # print(f"{history.x()}, {history.y()}")
            self.tft.fill_circle(self.history.x(), self.history.y(), 3, other_color)
        self.badge.set_front(self.color)

    async def run(self):
        self.setup_buttons()
        self.clear_screen()
        # set_up_buttons()
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
                if (x - prev_x) ** 2 + (y - prev_y) ** 2 > 5:
                    prev_x, prev_y = t
                    self.tft.fill_circle(x, y, 3, self.color.c565)
                    self.history.add_x_y(x, y)
        self.exit()

    async def exit(self):
        self.is_running = False
        self.badge.start_button.irq(None)
        self.badge.a_button.irq(None)
        self.badge.b_button.irq(None)
        self.badge.right_button.irq(None)
        self.badge.left_button.irq(None)
        self.badge.neopixels.fill((0, 0, 0))
        del self.history.points
        del self.history


# class Color:
#     def __init__(self, h, s, v):
#         # make the LEDs dimmer than the screen and boost their saturation
#         self.LED = lib.hsv_to_rgb(h, max(s, 0.8), min(v, 0.5))
#         self.c565 = lib.color565(*lib.hsv_to_rgb(h, s, v))


class PaintHistory:
    # TODO: make some kind of frame around the drawing area so it's only 255 x 240 so I can hold more dots in the history?
    def __init__(self):
        # index is the most recently written index of the history array
        self.index = 0
        # this is the latest valid index to fast forward to
        # if we've undone, it will not match the current index
        self.latest_valid_index = 0

        self.max_size = 20_000
        self.sleep_time = 1

        self.points = array("i", [0 for _ in range(self.max_size)])

    def clear(self):
        self.index = 0
        self.latest_valid_index = 0

    # def x_at(self, index):
    #     return self.points[index] >> 16

    # def y_at(self, index):
    #     return self.points[index] & 0x00_00_FF_FF

    def x(self):
        return (self.points[self.index] >> 16) & 0x00_00_FF_FF

    def y(self):
        return self.points[self.index] & 0x00_00_FF_FF

    def add_x_y(self, x, y):
        self.add_point((x << 16) | (y & 0x00_00_FF_FF))

    def add_point(self, p):
        self.index += 1
        if self.index >= self.max_size:
            # history.index = 0
            print("outta space")
            return
        self.points[self.index] = p
        self.latest_valid_index = self.index

    def get_point(self, index):
        return self.points[index]


# PaintProgram().run()
