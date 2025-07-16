# Add your own animations in here!
import board_config as bc
from lib.menu import MenuOption


# solid color
class ExampleAnimation:
    def __init__(self, color=(128, 10, 0), n=bc.NEOPIXEL_NUM_LEDS):
        self.color = color
        self.n = n

    def next(self):
        return [self.color] * self.n


animations = [
    MenuOption("Example", animation=ExampleAnimation()),
]
# animations = []
