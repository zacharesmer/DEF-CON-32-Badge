"""
A base class for a program that's mostly a menu

Supports paging, up, down, left, and right navigation
Unfortunately not holding down the buttons yet but I should really add it
"""

from machine import Pin
import asyncio
import time


class MenuProgram:
    def __init__(self, badge):
        self.badge = badge
        self.current_selection = 0
        self.options = []
        self.column_elements = 14
        self.num_columns = 2
        self.view_start = 0
        self.view_elements = self.column_elements * self.num_columns
        self.max_text_length = 16
        self.title = "Title"

    def setup_buttons(self):
        self.badge.up_button.irq(self.go_up, Pin.IRQ_FALLING)
        self.badge.down_button.irq(self.go_down, Pin.IRQ_FALLING)
        self.badge.a_button.irq(self.select, Pin.IRQ_FALLING)
        self.badge.left_button.irq(self.go_left, Pin.IRQ_FALLING)
        self.badge.right_button.irq(self.go_right, Pin.IRQ_FALLING)
        self.badge.b_button.irq(self.go_back, Pin.IRQ_FALLING)
        pass

    def un_setup_buttons(self):
        self.badge.up_button.irq(None)
        self.badge.down_button.irq(None)
        self.badge.a_button.irq(None)
        self.badge.left_button.irq(None)
        self.badge.right_button.irq(None)
        self.badge.b_button.irq(None)

    def go_up(self, arg):
        """
        handle up button press
        note to me so I don't mess this up a third time: the button is up, but the number goes *down*
        """
        first = True
        last_press = time.ticks_ms()
        while arg.value() == 0:
            if first or time.ticks_diff(time.ticks_ms(), last_press) > 200:
                first = False
                last_press = time.ticks_ms()

                self.current_selection = (self.current_selection - 1) % len(
                    self.options
                )
                if self.current_selection < self.view_start:
                    self.view_start = self.current_selection - self.column_elements + 1
                # this means it's wrapped around to the end
                if self.current_selection > self.view_start + self.view_elements:
                    self.view_start = (
                        len(self.options)
                        - (self.current_selection % self.view_elements)
                        - 1
                    )
                # print(self.current_selection)
                self.show()

    def go_down(self, arg):
        """
        handle up button press
        note to me so I don't mess this up a third time: the button is down, but the number goes *up*
        """
        # print("down")
        first = True
        last_press = time.ticks_ms()
        while arg.value() == 0:
            if first or time.ticks_diff(time.ticks_ms(), last_press) > 200:
                first = False
                last_press = time.ticks_ms()
                self.current_selection = (self.current_selection + 1) % len(
                    self.options
                )
                if self.current_selection >= self.view_start + self.view_elements:
                    self.view_start = self.current_selection
                # this means it's wrapped around to the beginning
                if self.current_selection < self.view_start:
                    self.view_start = 0
                # print(self.current_selection)
                self.show()

    def go_left(self, arg):
        # print("left")
        new_idx = self.current_selection - self.column_elements
        # print(new_idx)
        if new_idx >= 0:
            if new_idx < self.view_start:
                self.view_start -= self.view_elements
            self.current_selection = new_idx
            self.show()
            # print(self.current_selection)

    def go_right(self, arg):
        print("right")
        new_idx = self.current_selection + self.column_elements
        if new_idx < len(self.options):
            if new_idx >= self.view_start + self.view_elements:
                self.view_start += self.view_elements
            self.current_selection = new_idx
            # print(self.current_selection)
            self.show()

    def select(self, arg):
        print(f"Selected {self.current_selection}")

    def go_back(self, arg):
        self.is_running = False
        print("back")

    def show(self):
        left_margin = 10
        self.badge.screen.frame_buf.fill(self.badge.theme.bg1)
        max_title_length = 32
        if len(self.title) > max_title_length:
            display_title = f"...{self.title[len(self.title) - max_title_length:]}"
        else:
            display_title = self.title
        self.badge.screen.frame_buf.text(
            display_title, left_margin, 10, self.badge.theme.fg4
        )
        # print the options
        height = 30
        for i, opt in enumerate(
            self.options[self.view_start : self.view_start + self.view_elements]
        ):
            if i + self.view_start == self.current_selection:
                self.badge.screen.frame_buf.text(
                    ">", left_margin - 8, height, self.badge.theme.accent
                )
            self.badge.screen.frame_buf.text(
                opt.name[: self.max_text_length],
                left_margin,
                height,
                opt.color if opt.color is not None else self.badge.theme.fg1,
            )
            height += 15
            if height > 240 - 15:
                height = 30
                left_margin += 150

    async def run(self):
        self.setup_buttons()
        self.is_running = True
        self.show()
        while self.is_running:
            await asyncio.sleep(0)
        # teardown
        self.un_setup_buttons()
        del self.options

    async def exit(self):
        self.is_running = False


class MenuOption:
    """
    hold a display name, color, and any other properties that may be of use
    """

    def __init__(self, display_name, **kwargs):
        self.name = display_name
        # print(kwargs)
        # need this to be None if not explicitly set
        self.color = None
        for k, v in kwargs.items():
            setattr(self, k, v)
