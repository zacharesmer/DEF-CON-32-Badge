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
