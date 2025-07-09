from ws2812 import WS2812
from lib import hsv_to_rgb
import time

np = WS2812(auto_write=True)

h = 0

while True:
    for i in range(len(np)):
        color = hsv_to_rgb(h, .5, 0.1)
        print(color)
        np[i] = color
    h += 0.001
    if h > 1:
        h = 0
    time.sleep(0.01)
