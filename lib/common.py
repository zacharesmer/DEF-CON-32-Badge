from math import floor
import random
import board_config as bc


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

    def __getitem__(self, index):
        return self.RGB[index]


# not actually used yet
def nec_from_timings(timings):
    decoded = []
    tolerance = 0.3
    preamble_high = 9_000
    preamble_low = 4_500
    bit_high = 560
    one_low = 1_690
    zero_low = 560
    # 1 pulse preamble, 4 bytes that take 8 pulses each, and a stop pulse.
    # multiply by 2 except the stop bit because we are also counting gaps
    if len(timings) != 67:
        return None
    if not in_range(timings[0], preamble_high, tolerance):
        return None
    if not in_range(timings[1], preamble_low, tolerance):
        return None
    for t1, t2 in zip(timings[2::2], timings[3::2]):
        if not in_range(t1, bit_high, tolerance):
            return None
        if in_range(t2, one_low, tolerance):
            decoded.append(1)
        elif in_range(t2, zero_low, tolerance):
            decoded.append(0)
    # don't really care how long the stop pulse is if we made it here
    return decoded


def timings_from_nec(address, command, ext=False):
    if ext:
        bits = 16
    else:
        bits = 8
    # print(f"address: {address:08b}, command: {command:08b}")
    bit_high = 560
    one_low = 1_690
    zero_low = 560
    # preamble
    timings = [9000, 4500]
    # Send the least significant bit first
    mask = 0x1
    data_bytes = (address, ~address, command, ~command)
    for b in data_bytes:
        for _ in range(bits):
            if b & mask > 0:
                timings += [bit_high, one_low]
            else:
                timings += [bit_high, zero_low]
            b >>= 1
    # stop pulse
    timings.append(bit_high)
    return timings


def timings_from_necext(address, command):
    # print(f"address: {address:08b}, command: {command:08b}")
    bit_high = 560
    one_low = 1_690
    zero_low = 560
    # preamble
    timings = [9000, 4500]
    # the address is 32 bits but NEC uses 8 bits and sends the least significant first
    mask = 0x1
    inv_address = ~address
    for _ in range(8):
        if address & mask > 0:
            timings += [bit_high, one_low]
        else:
            timings += [bit_high, zero_low]
        address >>= 1
    for _ in range(8):
        if inv_address & mask > 0:
            timings += [bit_high, one_low]
        else:
            timings += [bit_high, zero_low]
        inv_address >>= 1
    inv_command = ~command
    for _ in range(8):
        if command & mask > 0:
            timings += [bit_high, one_low]
        else:
            timings += [bit_high, zero_low]
        command >>= 1
    for _ in range(8):
        if inv_command & mask > 0:
            timings += [bit_high, one_low]
        else:
            timings += [bit_high, zero_low]
        inv_command >>= 1
    # stop pulse
    timings.append(bit_high)
    return timings


def in_range(val, target, tolerance):
    return val < target * (1 + tolerance) and val > target * (1 - tolerance)


def int32_to_bytes(i):
    """Convert an integer to four bytes in little-endian format.
    from https://github.com/kentoj/python-fundamentals
    """
    return bytes((i & 0xFF, i >> 8 & 0xFF, i >> 16 & 0xFF, i >> 24 & 0xFF))
