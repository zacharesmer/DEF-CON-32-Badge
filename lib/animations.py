import random
import board_config as bc
import lib.common as common


class FadeThroughColors:
    def __init__(self, colors, n=bc.NEOPIXEL_NUM_LEDS):
        self.colors = colors
        # is increasing, current rgb value, which color in the list of colors it's targeting
        self.pixel_data = [
            FadeThroughPixel(max_rgb=colors[i % len(colors)], color_index=i)
            for i in range(n)
        ]
        self.n = n

    def next(self):
        result = []
        for i, px in enumerate(self.pixel_data):
            done, rgb = px.next()
            result.append(rgb)
            # move onto the next color
            if done:
                self.pixel_data[i].color_index = (
                    self.pixel_data[i].color_index + 1
                ) % len(self.colors)
                self.pixel_data[i].max_rgb = self.colors[self.pixel_data[i].color_index]
        return result


class FadeThroughPixel:
    def __init__(self, max_rgb, color_index):
        # for k, v in kwargs.items():
        #     setattr(self, k, v)
        self.color_index = color_index
        self.is_increasing = True
        self.rgb = [0, 0, 0]
        self.max_rgb = max_rgb

    def next(self):
        still_going = False
        if self.is_increasing:
            for comp in range(3):
                if self.rgb[comp] + 1 <= self.max_rgb[comp]:
                    self.rgb[comp] += 1
                    still_going = True
            if not still_going:
                self.is_increasing = False
        else:
            still_going = True
            for comp in range(3):
                if self.rgb[comp] - 1 >= 0:
                    self.rgb[comp] -= 1
                    # still_going = True
                else:
                    still_going = False
            if not still_going:
                self.is_increasing = True
        return ((not still_going) and self.is_increasing, self.rgb)

    def next_rainbow_wheel(self):
        pass


class RainbowParty:
    def __init__(self, step=0.005, n=bc.NEOPIXEL_NUM_LEDS):
        self.pixels = [RainbowWheelPixel(hue=i / n, step=step) for i in range(n)]

    def next(self):
        result = []
        for px in self.pixels:
            result.append(px.next())
        return result


class RainbowWheelPixel:
    def __init__(self, hue=0, step=0.005):
        self.hue = hue
        self.step = step

    def next(self):
        self.hue += self.step
        return common.hsv_to_rgb(self.hue, 1, 1)


class BlinkRed:
    def __init__(self, brightness=100, delay=1):
        self.brightness = brightness
        self.on = False
        self.count = 0
        self.delay = delay

    def next(self):
        self.count += 1
        if self.count == self.delay:
            self.on = not self.on
            self.count = 0
        if self.on:
            return (self.brightness, 0, 0)
        return (0, 0, 0)
