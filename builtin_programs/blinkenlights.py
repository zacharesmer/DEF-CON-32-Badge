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
        t = self.badge.theme
        self.options = [
            MenuOption(
                "Theme",
                animation=FadeThroughColors(
                    (t.fg1, t.fg2, t.fg3, t.fg4, t.accent, t.bg1, t.bg2)
                ),
            ),
            MenuOption("Rainbow Party", animation=RainbowParty()),
        ]
        try:
            extra_animations = __import__("extra_animations")
            for extra_option in extra_animations.animations:
                if hasattr(extra_option, "name") and hasattr(extra_option, "animation"):
                    self.options.append(extra_option)
                else:
                    print(
                        f"Animation not a valid MenuOption with animation attribute, not added."
                    )
                    print(f"option: {extra_option}")

        except ImportError as e:
            print(f"Error importing extra_animations: {e}")
            print("Creating extra_animations.py")
            with open("extra_animations.py", "w") as f:
                f.write(
                    '# # Add your own animations in here!\n\
# import board_config as bc\n\
# from lib.menu import MenuOption\n\
# # solid color\n\
# class ExampleAnimation:\n\
#     def __init__(self, color=(128, 10, 0), n=bc.NEOPIXEL_NUM_LEDS):\n\
#         self.color = color\n\
#         self.n = n\n\
#     def next(self):\n\
#         return [self.color] * self.n\n\
# animations = [MenuOption("Example", animation=ExampleAnimation())]\n\
animations = []\n'
                )
        self.title = "Das Blinkenlights"

    def show(self):
        super().show()
        self.badge.animation = self.options[self.current_selection].animation
