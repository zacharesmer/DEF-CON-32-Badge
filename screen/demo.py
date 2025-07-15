# Demo

import screen.st7789v as s
import screen.st7789v_definitions as defs
import screen.board_config as board_config
import random
import time
from screen.touch import Touchscreen
import lib.common as common

tft = s.ST7789V(manual_draw=True)
touch = Touchscreen()


# unfortunately there's no way to change the text size or font built into micropython
def sample_text():
    tft.frame_buf.fill(defs.BLACK)
    tft.frame_buf.text("Hello!", 10, 10, defs.WHITE)
    tft.frame_buf.text("Red text", 10, 40, defs.RED)
    tft.frame_buf.text("Green text", 10, 60, defs.GREEN)
    tft.frame_buf.text("Blue text", 10, 80, defs.BLUE)
    tft.frame_buf.text("Cyan text", 10, 100, defs.CYAN)
    tft.frame_buf.text("Magenta text", 10, 120, defs.MAGENTA)
    tft.frame_buf.text("Yellow text", 10, 140, defs.YELLOW)


# tft.frame_buf.text("hello!!!", 10, 10, defs.MAGENTA)
# tft.frame_buf.text("hello!!!", 10, 10, defs.MAGENTA)
# tft.frame_buf.text("hello!!!", 10, 10, defs.MAGENTA)
# tft.frame_buf.text("hello!!!", 10, 10, defs.MAGENTA)

sample_text()

tft.frame_buf.vline(
    board_config.SCREEN_WIDTH // 2, 0, board_config.SCREEN_HEIGHT, defs.WHITE
)


def random_dots():
    while True:
        tft.frame_buf.rect(8, board_config.SCREEN_HEIGHT - 24, 70, 14, defs.BLUE, True)
        # tft.frame_buf.text(
        #     f"{tft.fps:2.1f} fps", 10, board_config.SCREEN_HEIGHT - 20, defs.WHITE
        # )
        denom = random.random()
        r = round(50 ** (100 / 1 if (denom == 0) else denom))
        x = random.randint(
            board_config.SCREEN_WIDTH // 2 + r + 1, board_config.SCREEN_WIDTH - r - 2
        )
        y = random.randint(r + 1, board_config.SCREEN_HEIGHT - r - 2)
        color = common.color565(
            random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
        )
        tft.frame_buf.ellipse(x, y, r, r, color, True)
        ## uncomment this for touch screen, this function blocks until a touch is detected
        # print(touch.get_one_touch_in_pixels())
        tft.draw_frame()
        time.sleep(1 / 40)


def slide_down():
    r = 15
    x = board_config.SCREEN_WIDTH // 2 + 20
    y = r + 1
    y2 = r + 50
    y3 = r + 100
    color1 = common.color565(82, 21, 78)
    color2 = common.color565(71, 137, 44)
    color3 = common.color565(239, 48, 84)
    while True:
        tft.frame_buf.rect(8, board_config.SCREEN_HEIGHT - 24, 100, 14, defs.BLUE, True)
        # tft.frame_buf.text(
        #     f"{tft.fps:2.1f} fps", 10, board_config.SCREEN_HEIGHT - 20, defs.WHITE
        # )
        # clear the previous circle
        tft.frame_buf.ellipse(x, y, r, r, defs.BLACK, True)
        tft.frame_buf.ellipse(x + 60, y2, r, r, defs.BLACK, True)
        tft.frame_buf.ellipse(x + 120, y3, r, r, defs.BLACK, True)

        y = (y + 1) % (board_config.SCREEN_HEIGHT)
        y2 = (y2 + 1) % (board_config.SCREEN_HEIGHT)
        y3 = (y3 + 1) % (board_config.SCREEN_HEIGHT)

        # redraw
        tft.frame_buf.ellipse(x, y, r, r, color1, True)
        tft.frame_buf.ellipse(x + 60, y2, r, r, color2, True)
        tft.frame_buf.ellipse(x + 120, y3, r, r, color3, True)
        tft.draw_frame()
        time.sleep(1 / 40)


# slide_down()
random_dots()
