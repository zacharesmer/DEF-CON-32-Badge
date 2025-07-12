# TODO: factor out some reusable stuff for programs that are mostly a menu

from machine import Pin
from screen.st7789v_definitions import WHITE, BLACK
import asyncio


class MenuProgram:
    def __init__(self, badge):
        self.badge = badge
        self.current_selection = 0
        self.options = []
        self.column_elements = 15

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
        print("up")
        self.current_selection = (self.current_selection - 1) % len(self.options)
        self.show()

    def go_down(self, arg):
        print("down")
        self.current_selection = (self.current_selection + 1) % len(self.options)
        self.show()

    def go_left(self, arg):
        print("left")
        new_idx = self.current_selection - self.column_elements
        print(new_idx)
        if new_idx >= 0:
            self.current_selection = new_idx
        print(self.current_selection)
        self.show()

    def go_right(self, arg):
        print("right")
        new_idx = self.current_selection + self.column_elements
        if new_idx < len(self.options):
            self.current_selection = new_idx
        self.show()

    def select(self, arg):
        print(f"Selected {self.current_selection}")

    def go_back(self, arg):
        print("back")

    def show(self):
        left_margin = 40
        self.badge.screen.frame_buf.fill(BLACK)
        self.badge.screen.frame_buf.text(self.title, left_margin, 10, WHITE)
        # print the options
        height = 30
        for i, opt in enumerate(self.options):
            if i == self.current_selection:
                self.badge.screen.frame_buf.text(">", left_margin - 15, height, WHITE)
            self.badge.screen.frame_buf.text(opt[0], left_margin, height, WHITE)
            height += 15
            if height > 240 - 15:
                height = 15
                left_margin += 90

    async def run(self):
        self.setup_buttons()
        while self.is_running:
            await asyncio.sleep(0)
        await self.exit()

    async def exit(self):
        self.un_setup_buttons()
