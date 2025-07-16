import asyncio
from machine import Pin
import board_config as bc
from lib.menu import MenuProgram, MenuOption
from lib.animations import FadeThroughColors, RainbowParty


class Program(MenuProgram):
    """
    It wouldn't be a badge without blinkenlights
    """

    def __init__(self, badge):
        super().__init__(badge)
        self.options = [
            MenuOption("Theme"),
            MenuOption("Rainbow Party"),
        ]
        self.title = "Das Blinkenlights"

    def show(self):
        super().show()
        self.badge.animation = self.animation_factory(self.current_selection)

    def animation_factory(self, index):
        if index == 0:
            t = self.badge.theme
            return FadeThroughColors(
                (t.fg1, t.fg2, t.fg3, t.fg4, t.accent, t.bg1, t.bg2)
            )
        if index == 1:
            return RainbowParty()
