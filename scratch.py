# from ws2812 import WS2812
# from lib import hsv_to_rgb
# import time

# np = WS2812(auto_write=True)

# h = 0

# for i in range(len(np)):
#     print(i)
#     np[i] = (10, 0, 0)
#     time.sleep(2)

# while True:
#     for i in range(len(np)):
#         color = hsv_to_rgb(h, .5, 0.1)
#         print(color)
#         np[i] = color
#     h += 0.001
#     if h > 1:
#         h = 0
#     time.sleep(0.01)

import badge
import board_config as bc
import time
import color_selector
import asyncio
from lib.common import Color

badg = badge.DC32_Badge()

p = color_selector.ColorSelector(badg)


initial_color = Color(0, 20, 50, "rgb")


async def run():
    print(await p.get_color(initial_color))


asyncio.run(run())
# # recordings = []
# # with open("test.ir", "r") as f:
# #     recordings = p.read_ir_file(f)
while True:
    pass
