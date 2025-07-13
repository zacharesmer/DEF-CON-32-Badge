import time
import board_config as bc
import asyncio
from machine import Pin


class TextEntry:
    def __init__(self, badge):
        self.badge = badge
        self.key_height = 32
        self.key_width = 32
        self.kb_start_height = bc.SCREEN_HEIGHT - self.key_height * 4 - 10
        self.text_start_height = 32
        self.text_left_side = bc.SCREEN_WIDTH // 2 - 100
        self.caps = False
        self.text_entered = ""
        row0 = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        row1 = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]
        row2 = ["a", "s", "d", "f", "g", "h", "j", "k", "l", "OK"]
        row3 = ["^", "z", "x", "c", "v", "b", "n", "m", "_", "<"]
        self.rows = [row0, row1, row2, row3]
        pass

    def setup_buttons(self):
        self.badge.b_button.irq(self.go_back, Pin.IRQ_FALLING)

    def un_setup_buttons(self):
        self.badge.b_button.irq(None)

    def go_back(self, arg):
        # print("b")
        self.is_running = False

    # async def run(self):
    #     pass

    async def get_text(self, max_length):
        self.setup_buttons()
        self.show_keyboard()
        self.is_running = True
        last_letter_at = time.ticks_ms()
        while self.is_running:
            # print(f"running: {self.is_running}")
            t = self.badge.touch.get_one_touch_in_pixels()
            if t is not None:
                if time.ticks_diff(time.ticks_ms(), last_letter_at) > 500:
                    letter = self.letter_from_touch(t)
                    print(letter)
                    if letter == "^":
                        self.caps = not self.caps
                    elif letter == "<":
                        self.text_entered = self.text_entered[:-1]
                    elif letter == "OK":
                        if len(self.text_entered) > 0:
                            return self.text_entered
                    else:
                        if len(self.text_entered) < max_length:
                            self.text_entered = f"{self.text_entered}{letter}"
                    last_letter_at = time.ticks_ms()
                    self.show_keyboard()
            await asyncio.sleep(0)
        self.exit()

    async def exit(self):
        self.is_running = False
        self.un_setup_buttons()
        pass

    def show_keyboard(self):
        self.badge.screen.frame_buf.fill(bg_color + 0x6)
        self.badge.screen.frame_buf.text(
            self.text_entered, self.text_left_side, self.text_start_height, fg_color
        )
        height = self.kb_start_height
        left_position = 0
        for row in self.rows:
            for key in [k.upper() if self.caps else k for k in row]:
                self.badge.screen.frame_buf.rect(
                    left_position + 1, height + 1, 30, 30, bg_color
                )
                self.badge.screen.frame_buf.text(
                    key, left_position + 12, height + 12, fg_color
                )
                left_position += self.key_width
            left_position = 0
            height += self.key_height

    def letter_from_touch(self, t):
        x, y = t
        if (
            y < self.kb_start_height
            or y > self.kb_start_height + len(self.rows) * self.key_height
        ):
            # print("1")
            return None
        # figure out which letter was touched, or None if it wasn't any
        y_index = (y - self.kb_start_height) // self.key_height
        if y_index < len(self.rows) and y_index >= 0:
            x_index = x // self.key_width
            if x_index < len(self.rows[y_index]) and x_index >= 0:
                # print("2")
                letter = self.rows[y_index][x_index]
                if self.caps:
                    return letter.upper()
                return letter
                # return "a"
        # print("3")
        return None


bg_color = 0x00_00
fg_color = 0xFF_FF

# we've got 320 pixels of screen width to work with. Split it up into 32 pixel boxes I guess?

# 10 numbers
# 10 letters
# 9 letters
# 7 letters

# I also need an enter button and a space/underscore (cancel can just be the B button)
