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

badgey = badge.DC32_Badge()
# badgey.calibrate_touchscreen()

# import gc

# print(f"free: {gc.mem_free()}")
# gc.collect()
# print(f"free: {gc.mem_free()}")
# from paint import PaintProgram

# PaintProgram(badgey).run()


Weight_of_the_World = [
    (1 / 2, "L6"),
    (1 / 4, "3"),
    (1 / 4, "2"),
    (1 / 4, "2"),
    (1 / 2, "5"),
    (1 / 4, "L6"),
    (1 / 4, "L6"),
    (1 / 4, "3"),
    (1 / 4, "2"),
    (1 / 4, "5"),
    (1 / 1, "5"),
    (1 / 2, "L6"),
    (1 / 4, "3"),
    (1 / 4, "2"),
    (1 / 4, "2"),
    (1 / 2, "6"),
    (1 / 4, "2"),
    (1 / 4, "2"),
    (1 / 4, "3"),
    (1 / 4, "2"),
    (1 / 4, "6"),
    (1 / 1, "6"),
    (1 / 2, "L6"),
    (1 / 4, "3"),
    (1 / 4, "2"),
    (1 / 4, "2"),
    (1 / 2, "5"),
    (1 / 4, "L6"),
    (1 / 4, "L6"),
    (1 / 4, "3"),
    (1 / 4, "2"),
    (1 / 4, "5"),
    (1 / 1, "5"),
    (1 / 2, "L6"),
    (1 / 4, "3"),
    (1 / 4, "2"),
    (1 / 4, "2"),
    (1 / 2, "6"),
    (1 / 4, "2"),
    (1 / 4, "2"),
    (1 / 4, "3"),
    (1 / 4, "2"),
    (1 / 4, "6"),
    (1 / 1, "6"),
]

badgey.speaker.play(Weight_of_the_World, tempo=90, freq_multiple=1, output=0)
