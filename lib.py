from math import floor


# values are floats in range 0 to 1


def hsv_to_rgb(h, s, v):
    if s == 0.0:
        r = (v, v, v)
    i = int(h * 6.0)  # XXX assume int() truncates!
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    if i == 0:
        r = (v, t, p)
    if i == 1:
        r = (q, v, p)
    if i == 2:
        r = (p, v, t)
    if i == 3:
        r = (p, q, v)
    if i == 4:
        r = (t, p, v)
    if i == 5:
        r = (v, p, q)
    return [floor(c * 255) for c in r]


def color565(r, g, b):
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3


def color565_to_rgb(color):
    r = color >> 8
    g = (color >> 3) & 0x3
    b = color << 3
    return (r, g, b)


# for the touch screen calibration, but you could use it for other stuff too I guess
# pixel_value = m * touch_value + b
def lin_reg(pixels, touches):
    n = len(pixels)
    sum_t_squared = sum([t**2 for t in touches])
    sum_t_times_p = sum([t * p for t, p in zip(touches, pixels)])
    m = ((n * sum_t_times_p) - (sum(touches) * sum(pixels))) / (
        (n * sum_t_squared) - sum(touches) ** 2
    )
    b = (sum(pixels) - m * sum(touches)) / n
    return [m, b]


# def hsv_color565(h, s, v):
#     return color565(*hsv_to_rgb(h, s, v))

import random


class FadeRed:
    def __init__(self, max_brightness=100, speed=0.01):
        self.rgb = [0, 0, 0]
        self.max_brightness = max_brightness
        self.speed = speed
        self.increasing = True

    def next(self):
        if random.random() < self.speed:
            if self.rgb[0] >= self.max_brightness:
                self.increasing = False
            if self.rgb[0] <= 0:
                self.increasing = True
            if self.increasing:
                self.rgb[0] += 1
            else:
                self.rgb[0] -= 1
        return self.rgb


class BlinkRed:
    def __init__(self, brightness=100, delay=1):
        self.on = False
        self.count = 0
        self.delay = delay

    def next(self):
        self.count += 1
        if self.count == self.delay:
            self.on = not self.on
            self.count = 0
        if self.on:
            return (100, 0, 0)
        return (0, 0, 0)
