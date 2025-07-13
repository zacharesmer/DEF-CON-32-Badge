"""
A base class for a program that's mostly a menu

Supports paging, up, down, left, and right navigation
Unfortunately not holding down the buttons yet but I should really add it
"""

from machine import Pin
from screen.st7789v_definitions import WHITE, BLACK
import asyncio


class MenuProgram:
    def __init__(self, badge):
        self.badge = badge
        self.current_selection = 0
        # self.options = []
        self.column_elements = 14
        self.num_columns = 2
        self.view_start = 0
        self.view_elements = self.column_elements * self.num_columns
        self.max_text_length = 16

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
        self.current_selection = (self.current_selection - 1) % len(self.options)
        if self.current_selection < self.view_start:
            self.view_start = self.current_selection - self.column_elements + 1
        print(self.current_selection)
        self.show()

    def go_down(self, arg):
        """
        handle up button press
        note to me so I don't mess this up a third time: the button is down, but the number goes *up*
        """
        # print("down")
        self.current_selection = (self.current_selection + 1) % len(self.options)
        if self.current_selection >= self.view_start + self.view_elements:
            self.view_start = self.current_selection
        print(self.current_selection)
        self.show()

    def go_left(self, arg):
        # print("left")
        new_idx = self.current_selection - self.column_elements
        # print(new_idx)
        if new_idx >= 0:
            if new_idx < self.view_start:
                self.view_start -= self.view_elements
            self.current_selection = new_idx
        print(self.current_selection)
        self.show()

    def go_right(self, arg):
        print("right")
        new_idx = self.current_selection + self.column_elements
        if new_idx < len(self.options):
            if new_idx >= self.view_start + self.view_elements:
                self.view_start += self.view_elements
            self.current_selection = new_idx
        print(self.current_selection)
        self.show()

    def select(self, arg):
        print(f"Selected {self.current_selection}")

    def go_back(self, arg):
        self.view_start = 0
        print("back")

    def show(self):
        left_margin = 10
        self.badge.screen.frame_buf.fill(BLACK)
        self.badge.screen.frame_buf.text(self.title, left_margin, 10, WHITE)
        # print the options
        height = 30
        for i, opt in enumerate(
            self.options[self.view_start : self.view_start + self.view_elements]
        ):
            if i + self.view_start == self.current_selection:
                self.badge.screen.frame_buf.text(">", left_margin - 8, height, WHITE)
            self.badge.screen.frame_buf.text(
                opt[0][: self.max_text_length], left_margin, height, WHITE
            )
            height += 15
            if height > 240 - 15:
                height = 30
                left_margin += 150

    async def run(self):
        self.setup_buttons()
        self.is_running = True
        while self.is_running:
            await asyncio.sleep(0)
        await self.exit()

    async def exit(self):
        self.un_setup_buttons()
