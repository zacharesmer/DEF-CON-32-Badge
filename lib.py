from math import floor
import random


# from Python colorsys library, approximately
# takes in floats in range 0.0 to 1.0, returns ints 0-255
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


# takes values 0-255, returns floats 0.0-1.0
def rgb_to_hsv(r, g, b):
    maxc = max(r, g, b)
    minc = min(r, g, b)
    rangec = maxc - minc
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = rangec / maxc
    rc = (maxc - r) / rangec
    gc = (maxc - g) / rangec
    bc = (maxc - b) / rangec
    if r == maxc:
        h = bc - gc
    elif g == maxc:
        h = 2.0 + rc - bc
    else:
        h = 4.0 + gc - rc
    h = (h / 6.0) % 1.0
    return h, s, v


# from Russ Hughes st7789 driver
def color565(r, g, b):
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3


def color565_to_rgb(color):
    r = color >> 8
    g = (color >> 3) & 0x3
    b = color << 3
    return (r, g, b)


# for the touch screen calibration, but you could use it for other stuff too I guess
# pixel_value = m * touch_value + b
def lin_reg(x, y):
    n = len(x)
    sum_t_squared = sum([t**2 for t in y])
    sum_t_times_p = sum([t * p for t, p in zip(y, x)])
    m = ((n * sum_t_times_p) - (sum(y) * sum(x))) / ((n * sum_t_squared) - sum(y) ** 2)
    b = (sum(x) - m * sum(y)) / n
    return [m, b]


# def hsv_color565(h, s, v):
#     return color565(*hsv_to_rgb(h, s, v))


def shitty_wrap_text(text, chars_wide):
    """
    There is a cpython library to do this well but I'm going to do it badly.
    Completely ignores spaces and breaks words at random places
    badness >>>>>> 10,000
    """
    return [
        text[y - chars_wide : y]
        for y in range(chars_wide, len(text) + chars_wide, chars_wide)
    ]


class Color:
    """
    Convenience class to hold an RGB and a 565 representation for easy use with LEDs and with the screen
    """

    def __init__(self, a, b, c, init_type="rgb"):
        # use HSL and adjust the LED brightness for the paint app
        if init_type == "paint":
            # make the LEDs dimmer than the screen and boost their saturation
            self.RGB = hsv_to_rgb(a, max(b, 0.8), min(c, 0.5))
            self.c565 = color565(*hsv_to_rgb(a, b, c))
        if init_type == "rgb":
            self.RGB = (a, b, c)
            self.c565 = color565(a, b, c)

    def __int__(self):
        return self.c565

    def __iter__(self):
        return iter(self.RGB)


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
