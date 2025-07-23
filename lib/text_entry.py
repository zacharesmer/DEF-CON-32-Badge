import time
import board_config as bc
import asyncio
from machine import Pin

# TODO add optional button support like the color chooser


class TextEntry:
    def __init__(self, badge, max_length=16, prompt="Enter text:"):
        self.badge = badge
        self.max_length = max_length
        self.prompt = prompt
        self.key_height = 32
        self.key_width = 32
        self.kb_start_height = bc.SCREEN_HEIGHT - self.key_height * 4 - 10
        self.prompt_start_height = self.kb_start_height - 64
        self.text_start_height = self.kb_start_height - 32
        self.text_left_side = 32
        self.caps = False
        self.text_entered = ""
        row0 = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        row1 = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]
        row2 = ["a", "s", "d", "f", "g", "h", "j", "k", "l", "OK"]
        row3 = ["^", "z", "x", "c", "v", "b", "n", "m", "_", "<"]
        self.rows = [row0, row1, row2, row3]
        self.selected_key = [0, 0]
        self.selection_made = False
        pass

    def setup_buttons(self):
        self.badge.b_button.irq(self.go_back, Pin.IRQ_FALLING)
        self.badge.a_button.irq(self.select, Pin.IRQ_FALLING)
        self.badge.left_button.irq(self.go_left, Pin.IRQ_FALLING)
        self.badge.right_button.irq(self.go_right, Pin.IRQ_FALLING)
        self.badge.up_button.irq(self.go_up, Pin.IRQ_FALLING)
        self.badge.down_button.irq(self.go_down, Pin.IRQ_FALLING)

    def un_setup_buttons(self):
        self.badge.b_button.irq(None)
        self.badge.a_button.irq(None)
        self.badge.left_button.irq(None)
        self.badge.right_button.irq(None)
        self.badge.up_button.irq(None)
        self.badge.down_button.irq(None)

    def go_back(self, arg):
        print("b")
        self.is_running = False

    def select(self, arg):
        print("a")
        self.selection_made = True

    def go_left(self, arg):
        print("left")
        first = True
        last_press = time.ticks_ms()
        while arg.value() == 0:
            if first or time.ticks_diff(time.ticks_ms(), last_press) > 200:
                first = False
                last_press = time.ticks_ms()
                self.selected_key[1] = (self.selected_key[1] - 1) % len(self.rows[0])
                self.show_keyboard(keyboard=True)

    def go_right(self, arg):
        print("right")
        first = True
        last_press = time.ticks_ms()
        while arg.value() == 0:
            if first or time.ticks_diff(time.ticks_ms(), last_press) > 200:
                first = False
                last_press = time.ticks_ms()
                self.selected_key[1] = (self.selected_key[1] + 1) % len(self.rows[0])
                self.show_keyboard(keyboard=True)

    def go_up(self, arg):
        print("up")
        # physically up on the screen, number goes down
        first = True
        last_press = time.ticks_ms()
        while arg.value() == 0:
            if first or time.ticks_diff(time.ticks_ms(), last_press) > 200:
                first = False
                last_press = time.ticks_ms()
                self.selected_key[0] = (self.selected_key[0] - 1) % len(self.rows)
                self.show_keyboard(keyboard=True)

    def go_down(self, arg):
        print("down")
        first = True
        last_press = time.ticks_ms()
        while arg.value() == 0:
            if first or time.ticks_diff(time.ticks_ms(), last_press) > 200:
                first = False
                last_press = time.ticks_ms()
                self.selected_key[0] = (self.selected_key[0] + 1) % len(self.rows)
                self.show_keyboard(keyboard=True)

    async def get_text(self):
        self.setup_buttons()
        self.show_keyboard(True, True)
        self.is_running = True
        last_letter_at = time.ticks_ms()
        while self.is_running:
            if time.ticks_diff(time.ticks_ms(), last_letter_at) > 500:
                t = self.badge.touch.get_one_touch_in_pixels()
                if t is not None:
                    self.set_selected_key_from_touch(t)
                    last_letter_at = time.ticks_ms()
            if self.selection_made:
                self.selection_made = False
                letter = self.rows[self.selected_key[0]][self.selected_key[1]]
                if self.caps:
                    letter = letter.upper()
                if letter == "^":
                    self.caps = not self.caps
                elif letter == "<":
                    self.text_entered = self.text_entered[:-1]
                elif letter == "OK":
                    if len(self.text_entered) > 0:
                        return self.text_entered
                else:
                    if len(self.text_entered) < self.max_length:
                        self.text_entered = f"{self.text_entered}{letter}"
                self.show_keyboard(entered_text=True)
            await asyncio.sleep(0)
        self.exit()

    async def exit(self):
        self.is_running = False
        self.un_setup_buttons()
        pass

    # to reduce flickering, choose whether to redraw the text area, the keyboard, both, or neither
    def show_keyboard(self, entered_text=True, keyboard=True):

        if keyboard:
            self.badge.screen.frame_buf.fill(self.badge.theme.bg2)

        elif entered_text:
            self.badge.screen.frame_buf.rect(
                0,
                0,
                bc.SCREEN_WIDTH,
                self.kb_start_height - 1,
                self.badge.theme.bg2,
                True,
            )

        if entered_text:

            self.badge.screen.frame_buf.text(
                self.text_entered,
                self.text_left_side,
                self.text_start_height,
                self.badge.theme.fg1,
            )
            # show a lil cursor
            if len(self.text_entered) < self.max_length:
                self.badge.screen.frame_buf.rect(
                    self.text_left_side + 8 * len(self.text_entered),
                    self.text_start_height - 8,
                    8,
                    16,
                    self.badge.theme.fg2,
                    True,
                )
            self.badge.screen.frame_buf.text(
                self.prompt,
                self.text_left_side,
                self.prompt_start_height,
                self.badge.theme.fg1,
            )
        if keyboard:
            height = self.kb_start_height
            left_position = 0
            for row_i, row in enumerate(self.rows):
                for key_i, key in enumerate(
                    [k.upper() if self.caps else k for k in row]
                ):
                    if self.selected_key == [row_i, key_i]:
                        box_color = self.badge.theme.accent
                    else:
                        box_color = self.badge.theme.fg2
                    self.badge.screen.text_in_box(
                        key,
                        left_position + 1,
                        height + 1,
                        self.badge.theme.fg1,
                        box_color,
                        box_width=30,
                        box_height=30,
                        fill=False,
                    )
                    left_position += self.key_width
                left_position = 0
                height += self.key_height
        self.badge.screen.draw_frame()

    def set_selected_key_from_touch(self, t):
        """check if touch is None before calling this"""
        x, y = t
        # quit early if the touch was outside of the keyboard
        if (
            y < self.kb_start_height
            or y > self.kb_start_height + len(self.rows) * self.key_height
        ):
            return
        # figure out which letter was touched
        y_index = (y - self.kb_start_height) // self.key_height
        if y_index < len(self.rows) and y_index >= 0:
            x_index = x // self.key_width
            if x_index < len(self.rows[y_index]) and x_index >= 0:
                self.selected_key = [y_index, x_index]
                self.selection_made = True
                return


# bg_color = 0x00_00
# secondary_bg_color = bg_color + 0x6
# fg_color = 0xFF_FF

# we've got 320 pixels of screen width to work with. Split it up into 32 pixel boxes I guess?

# 10 numbers
# 10 letters
# 9 letters
# 7 letters

# I also need an enter button and a space/underscore (cancel can just be the B button)
