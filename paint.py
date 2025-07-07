from pirda.irda import IrDA_UART
import board_config
import time
from screen.touch import Touchscreen
import screen.st7789v as st7789
from machine import Pin, Timer
import random
from array import array


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


def clear_screen(*args):
    global color
    global bg_color
    global history
    color = random_fg_color()
    bg_color = random_bg_color()
    # TODO make some fun effects for coloring in the new background color (random lines, dots, etc.)
    tft.fill(bg_color)
    # tft.frame_buf.text(f"{bg_color:016b}", 50, 50, color)
    history.clear()


def calibrate():
    tft.fill_circle(20, 20, 5, st7789.MAGENTA)
    x1, y1 = touch.get_one_touch(verbose=True)
    time.sleep(0.6)
    tft.fill_circle(300, 220, 5, st7789.MAGENTA)
    x2, y2 = touch.get_one_touch(verbose=True)
    # TODO fit a line to these data points and actually use it to set the calibration values in case they are different for different badges
    clear_screen()


class PaintHistory:
    # TODO: make some kind of frame around the drawing area so it's only 255 x 240 so I can hold more dots in the history
    # or if I want to be boring just send the framebuf (boooo)
    def __init__(self):
        self.index = 0
        self.latest_valid_index = 0

        self.max_size = 10_000
        self.sleep_time = 1

        self.x = array("i", [0] * 10_000)
        self.y = array("i", [0] * 10_000)

    def clear(self):
        history.index = 0
        history.latest_valid_index = 0


# these are standalone methods because I don't want to figure out how to use an object method in a callback
# lol turns out it's easy I guess I should go fix that


def go_back(*args):
    global history
    print(args)
    while args[0].value() == 0:
        if history.index > 0:
            history.index -= 1
            # erase the pixel
            tft.fill_circle(
                history.x[history.index],
                history.y[history.index],
                3,
                bg_color,
            )
            time.sleep(history.sleep_time)


def go_back_async(*args):
    # if the button has stopped being pressed, stop going back
    if args[0].value() != 0:
        return
    global history
    button = args[0]
    if history.index > 0:
        history.index -= 1
        # erase the pixel
        tft.fill_circle(
            history.x[history.index],
            history.y[history.index],
            3,
            bg_color,
        )
        Timer(
            mode=Timer.ONE_SHOT,
            period=history.sleep_time,
            callback=lambda *args: go_back_async(button),
        )


def go_forward(*args):
    global history
    while args[0].value() == 0:
        if history.index < history.latest_valid_index:
            tft.fill_circle(
                history.x[history.index], history.y[history.index], 3, color
            )
            history.index += 1
            time.sleep(history.sleep_time)


def go_forward_async(*args):
    # if the button has stopped being pressed, stop going forward
    if args[0].value() != 0:
        return
    global history
    button = args[0]
    if history.index < history.latest_valid_index:
        tft.fill_circle(history.x[history.index], history.y[history.index], 3, color)
        history.index += 1
        Timer(
            mode=Timer.ONE_SHOT,
            period=history.sleep_time,
            callback=lambda *args: go_forward_async(button),
        )


# conversion functions to translate between touch sensor size and screen size


def send_drawing(*args):
    irda_uart.reset_machines()
    print(f"Sending size: {history.index}")
    irda_uart.send_word(history.index)
    time.sleep(history.sleep_time)
    irda_uart.send_word(color)
    time.sleep(history.sleep_time)
    for i in range(history.index):
        p_x = history.x[i]
        p_y = history.y[i]
        print(f"{(p_x << 16) | p_y:032b}")
        irda_uart.send_word((p_x << 16) | p_y)
        # time.sleep(history.sleep_time)


def receive_drawing(*args):
    irda_uart.reset_machines()
    size = None
    other_color = None
    rxed = 0
    global history
    while size is None and args[0].value() == 0:
        size = irda_uart.receive_word()
        if size is not None:
            print(size)
    if size is None:
        # print("No size :(")
        return
    print(f"{size:032b}")
    while other_color is None and args[0].value() == 0:
        other_color = irda_uart.receive_word()
        if other_color is not None:
            print(other_color)
    if other_color is None:
        # print("No size :(")
        return
    while args[0].value() == 0 and rxed < size:
        val = None
        while val is None and args[0].value() == 0:
            val = irda_uart.receive_word()
        if val is None:
            break
        p_y = val & 0x00_00_FF_FF
        p_x = val >> 16
        # print(f"{val:032b}")
        # print(f"{p_x}, {p_y}")
        tft.pixel(p_x, p_y, other_color)
        history.x[history.index + rxed] = p_x
        history.y[history.index + rxed] = p_y
        rxed += 1
        # print(f"Received {rxed} of {size} words")
    # now fill in the pixel lines with better ones
    for _ in range(rxed):
        # print("what's happening")
        tft.fill_circle(
            history.x[history.index], history.y[history.index], 3, other_color
        )
        # print("how many times")
        history.index += 1
        history.latest_valid_index = history.index


def set_up_buttons():
    start_button = Pin(board_config.START_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
    start_button.irq(clear_screen, trigger=Pin.IRQ_FALLING)

    a_button = Pin(board_config.A_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
    a_button.irq(go_forward_async, trigger=Pin.IRQ_FALLING)

    b_button = Pin(board_config.B_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
    b_button.irq(go_back_async, trigger=Pin.IRQ_FALLING)

    right_button = Pin(board_config.RIGHT_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
    right_button.irq(send_drawing, trigger=Pin.IRQ_FALLING)

    left_button = Pin(board_config.LEFT_BUTTON, mode=Pin.IN, pull=Pin.PULL_UP)
    left_button.irq(receive_drawing, trigger=Pin.IRQ_FALLING)


irda_uart = IrDA_UART(board_config.IRDA_TX_PIN, board_config.IRDA_RX_PIN, 115200)
# real_ish_spi = SoftSPI(
#     baudrate=62_500_000,
#     polarity=1,
#     phase=1,
#     sck=Pin(board_config.DISPLAY_SCK_PIN, Pin.OUT),
#     mosi=Pin(board_config.DISPLAY_DO_PIN, Pin.OUT),
#     miso=Pin(28),
# )  # SoftSPI needs a MISO pin, used one of the gpio on the SAO
# spi = PIO_SPI()
tft = st7789.ST7789V()
# tft.init()
touch = Touchscreen()
history = PaintHistory()

color = random_fg_color()
bg_color = random_bg_color()


def run():
    set_up_buttons()
    clear_screen()
    while True:
        x, y = touch.get_one_touch_in_pixels(verbose=False)
        # tft.pixel(p_x, p_y, color)
        tft.fill_circle(x, y, 3, color)
        history.x[history.index] = x
        history.y[history.index] = y
        history.index += 1
        if history.index == history.max_size:
            history.index = 0
            print("outta space")
        history.latest_valid_index = history.index
        # tft.draw_frame()
        # time.sleep(1 / 40)


run()
