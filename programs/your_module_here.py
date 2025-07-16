import asyncio
from machine import Pin
import board_config as bc
from lib.animations import RainbowParty


class Program:
    """
    Example program

    There's a strong argument to be made that all programs should inherit from something like this,
    so if you want to make a child class, go for it. Also look at MenuProgram in menu.py; it
    may be a more useful thing to inherit from.
    """

    def __init__(self, badge):
        self.badge = badge
        self.setup_buttons()

    def setup_buttons(self):
        # use Pin.IRQ_FALLING so it only triggers when the button is first pressed
        self.badge.b_button.irq(self.go_back, Pin.IRQ_FALLING)

    def un_setup_buttons(self):
        self.badge.b_button.irq(None)

    # callbacks need one extra argument
    def go_back(self, arg):
        print(f"{arg} falling edge")
        self.is_running = False

    async def run(self):
        self.is_running = True
        self.badge.screen.frame_buf.rect(
            40,
            40,
            bc.SCREEN_WIDTH - 80,
            bc.SCREEN_HEIGHT - 80,
            self.badge.theme.accent,
            True,
        )
        self.badge.screen.text_in_box(
            "Edit programs.json to add a program to the menu!",
            50,
            50,
            self.badge.theme.fg2,
            self.badge.theme.bg2,
            box_width=bc.SCREEN_WIDTH - 100,
            box_height=bc.SCREEN_HEIGHT - 100,
            fill=True,
        )
        self.badge.screen.draw_frame()
        self.badge.animation = RainbowParty()
        while self.is_running:
            await asyncio.sleep(0)
        # after this loop exits clean up anything like interrupts and animations.
        # The main menu will also try to clean these up but it may not have accounted for everything
        self.un_setup_buttons()
        self.badge.animation = None

    async def exit(self):
        """
        This is called when the menu needs to kill the program
        """
        self.is_running = False
