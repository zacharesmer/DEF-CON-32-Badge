from pirda.irda import IrDA_UART
import board_config
import time
from screen.touch import Touchscreen
import screen.st7789v as st7789
from machine import Pin, Timer
import random
from array import array
import rp2
from ws2812 import WS2812

import asyncio

# import micropython
# micropython.alloc_emergency_exception_buf(100)


def random_fg_color():
    # TODO make this prettier
    return st7789.color565(
        random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)
    )


def random_bg_color():
    # TODO make this prettier
    return st7789.color565(
        random.randint(0, 80), random.randint(0, 80), random.randint(0, 80)
    )


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

        self.np = WS2812()

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


# these are standalone methods because I don't want to figure out how to use an object method in a callback
# lol turns out it's easy I guess I should go fix that


class PaintProgram:
    def __init__(self):
        self.irda_uart = IrDA_UART(
            board_config.IRDA_TX_PIN, board_config.IRDA_RX_PIN, 19200
        )
        self.tft = st7789.ST7789V()
        self.touch = Touchscreen()
        self.history = PaintHistory()
        self.setup_buttons()
        self.color = random_fg_color()
        self.bg_color = random_bg_color()

    def setup_buttons(self):
        self.start_button = Pin(
            board_config.START_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP
        )
        self.start_button.irq(self.clear_screen, trigger=Pin.IRQ_FALLING)

        self.a_button = Pin(board_config.A_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self.a_button.irq(self.go_forward, trigger=Pin.IRQ_FALLING)

        self.b_button = Pin(board_config.B_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self.b_button.irq(self.go_back, trigger=Pin.IRQ_FALLING)

        self.right_button = Pin(
            board_config.RIGHT_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP
        )
        self.right_button.irq(self.send_drawing, trigger=Pin.IRQ_FALLING)

        self.left_button = Pin(board_config.LEFT_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
        self.left_button.irq(self.receive_drawing, trigger=Pin.IRQ_FALLING)

    def clear_screen(self, *args):
        self.color = random_fg_color()
        self.bg_color = random_bg_color()
        # TODO make some fun effects for coloring in the new background color (random lines, dots, etc.)
        self.tft.fill(self.bg_color)
        # tft.frame_buf.text(f"{bg_color:016b}", 50, 50, color)
        self.history.clear()

    def calibrate(self):
        self.tft.fill_circle(20, 20, 5, st7789.MAGENTA)
        x1, y1 = self.touch.get_one_touch(verbose=True)
        time.sleep(0.6)
        self.tft.fill_circle(300, 220, 5, st7789.MAGENTA)
        x2, y2 = self.touch.get_one_touch(verbose=True)
        # TODO fit a line to these data points and actually use it to set the calibration values in case they are different for different badges
        self.clear_screen()

    def go_back(self, *args):
        print(args)
        while args[0].value() == 0:
            if self.history.index > 0:
                # erase the pixel
                self.tft.fill_circle(
                    self.history.x(),
                    self.history.y(),
                    3,
                    self.bg_color,
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
                self.bg_color,
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
                self.tft.fill_circle(self.history.x(), self.history.y(), 3, self.color)
                time.sleep_ms(self.history.sleep_time)

    def go_forward_async(self, *args):
        # if the button has stopped being pressed, stop going forward
        if args[0].value() != 0:
            return
        button = args[0]
        if self.history.index < self.history.latest_valid_index:
            self.history.index += 1
            self.tft.fill_circle(self.history.x(), self.history.y(), 3, self.color)
            Timer(
                mode=Timer.ONE_SHOT,
                period=self.history.sleep_time,
                callback=lambda *args: self.go_forward_async(button),
            )

    def send_drawing(self, *args):
        self.irda_uart.reset_machines()
        print(f"Sending size: {self.history.index}")
        send_start = time.time_ns()
        self.irda_uart.send_word(self.history.index)
        asyncio.sleep_ms(self.history.sleep_time)
        # time.sleep_ms(history.sleep_time)
        self.irda_uart.send_word(self.color)
        asyncio.sleep_ms(self.history.sleep_time)
        # time.sleep_ms(history.sleep_time)
        for i in range(1, self.history.index + 1):
            # p_x = history.x[i]
            # p_y = history.y[i]
            # print(f"{history.get_point(i):032b}")
            self.irda_uart.send_word(self.history.get_point(i))

        print("sent")
        print(f"took {(time.time_ns() - send_start)/10**6} ms")
        # print("why so slow??")

    def receive_drawing(self, *args):
        print("receiving...")
        self.irda_uart.reset_machines()
        size = None
        other_color = None
        rxed = 0
        while size is None and args[0].value() == 0:
            size = self.irda_uart.receive_word()
            if size is not None:
                print(size)
            # asyncio.sleep(0)
        if size is None:
            print("No size :(")
            return
        print(f"{size:032b}")
        while other_color is None and args[0].value() == 0:
            other_color = self.irda_uart.receive_word()
            if other_color is not None:
                print(other_color)
            # asyncio.sleep(0)
        if other_color is None:
            print("No color :(")
            return
        while args[0].value() == 0 and rxed < size:
            val = None
            while val is None and args[0].value() == 0:
                val = self.irda_uart.receive_word()
                if val is None:
                    print("wait")
            if val is None:
                break
            # print(f"{val:032b}")
            self.history.add_point(val)
            rxed += 1
            # print(f"{history.x()}, {history.y()}")
            self.tft.fill_circle(self.history.x(), self.history.y(), 3, other_color)

    def run(self):
        # set_up_buttons()
        self.clear_screen()
        prev_x, prev_y = (0, 0)
        while True:
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
                    self.tft.fill_circle(x, y, 3, self.color)
                    self.history.add_x_y(x, y)


PaintProgram().run()
