""" """

import lib.common as common
from machine import Pin
import time


class ColorSelector:
    def __init__(self, badge):
        self.badge = badge
        self.h = 1.0
        self.s = 1.0
        self.v = 1.0
        self.h_start_height = 20
        self.s_start_height = 90
        self.v_start_height = 160
        self.gradient_left_start = 20
        self.gradient_width = 200
        self.gradient_height = 50
        self.focused_gradient = 0
        self.step = 1 / self.gradient_width
        self.selection_made = False
        self.ok_button_top = self.v_start_height
        self.ok_button_left = self.gradient_left_start + self.gradient_width + 20
        self.ok_button_size = self.gradient_height

    def setup_buttons(self):
        self.badge.b_button.irq(self.go_back, Pin.IRQ_FALLING)
        self.badge.up_button.irq(self.go_up, Pin.IRQ_FALLING)
        self.badge.down_button.irq(self.go_down, Pin.IRQ_FALLING)
        self.badge.a_button.irq(self.select, Pin.IRQ_FALLING)
        self.badge.left_button.irq(self.go_left, Pin.IRQ_FALLING)
        self.badge.right_button.irq(self.go_right, Pin.IRQ_FALLING)

    def un_setup_buttons(self):
        self.badge.b_button.irq(None)

    def go_up(self, arg):
        self.focused_gradient = (self.focused_gradient - 1) % 3
        self.show(False, False, False)
        pass

    def go_down(self, arg):
        self.focused_gradient = (self.focused_gradient + 1) % 3
        self.show(False, False, False)
        pass

    def go_left(self, arg):
        times = 0
        while arg.value() == 0:
            if self.focused_gradient == 0:
                self.h = max(self.h - self.step, 0)
                # hack: only redraw every 5 steps to speed it up
                if times % 5 == 0:
                    self.show(False, True, False)
            elif self.focused_gradient == 1:
                self.s = max(self.s - self.step, 0)
                self.show(False, False, False)
            elif self.focused_gradient == 2:
                self.v = max(self.v - self.step, 0)
                self.show(False, False, False)
            # time.sleep_ms(5)
            times += 1
        self.show(False, False, False)

    def go_right(self, arg):
        times = 0
        while arg.value() == 0:
            if self.focused_gradient == 0:
                self.h = min(self.h + self.step, 1)
                # hack: only redraw every 5 steps to speed it up
                if times % 5 == 0:
                    self.show(False, True, False)
            elif self.focused_gradient == 1:
                self.s = min(self.s + self.step, 1)
                self.show(False, False, False)
            elif self.focused_gradient == 2:
                self.v = min(self.v + self.step, 1)
                self.show(False, False, False)
            times += 1
        self.show(False, False, False)

    def go_back(self, arg):
        # print("b")
        self.is_running = False

    def select(self, arg):
        self.selection_made = True

    async def get_color(self, initial_color=None):
        if initial_color is not None:
            self.h, self.s, self.v = common.rgb_to_hsv(*initial_color)
        print(self.h, self.s, self.v)
        self.setup_buttons()
        self.badge.screen.fill(self.badge.theme.bg1)
        self.show()
        self.is_running = True
        while self.is_running:
            t = self.badge.touch.get_one_touch_in_pixels()
            if t is not None:
                self.set_color_from_touch(t)
            if self.selection_made:
                return common.hsv_to_rgb(self.h, self.s, self.v)
        return None

    def show(self, h=True, s=True, v=True):
        # draw outlines and a little indicator of the current selections
        for i, start_height in enumerate(
            (self.h_start_height, self.s_start_height, self.v_start_height)
        ):
            if i == self.focused_gradient:
                color = self.badge.theme.fg1
            else:
                color = self.badge.theme.bg1
            self.badge.screen.frame_buf.rect(
                self.gradient_left_start - 1,
                start_height - 1,
                self.gradient_width + 2,
                self.gradient_height + 2,
                color,
            )
        # h indicator
        self.badge.screen.frame_buf.rect(
            self.gradient_left_start - 5,
            self.h_start_height + self.gradient_height + 1,
            self.gradient_width + 10,
            10,
            self.badge.theme.bg1,
            True,
        )
        self.badge.screen.frame_buf.text(
            "^",
            self.gradient_left_start + round(self.h * self.gradient_width) - 4,
            self.h_start_height + self.gradient_height + 1,
            self.badge.theme.fg1,
        )
        # s indicator
        self.badge.screen.frame_buf.rect(
            self.gradient_left_start - 5,
            self.s_start_height + self.gradient_height + 1,
            self.gradient_width + 10,
            10,
            self.badge.theme.bg1,
            True,
        )
        self.badge.screen.frame_buf.text(
            "^",
            self.gradient_left_start + round(self.s * self.gradient_width) - 4,
            self.s_start_height + self.gradient_height + 1,
            self.badge.theme.fg1,
        )
        # v indicator
        self.badge.screen.frame_buf.rect(
            self.gradient_left_start - 5,
            self.v_start_height + self.gradient_height + 1,
            self.gradient_width + 10,
            10,
            self.badge.theme.bg1,
            True,
        )
        self.badge.screen.frame_buf.text(
            "^",
            self.gradient_left_start + round(self.v * self.gradient_width) - 4,
            self.v_start_height + self.gradient_height + 1,
            self.badge.theme.fg1,
        )

        # draw H S V gradients
        if h:
            hue = 0
            y = self.h_start_height
            for x in range(
                self.gradient_left_start, self.gradient_left_start + self.gradient_width
            ):
                color = common.color565(*common.hsv_to_rgb(hue, 1, 1))
                self.badge.screen.frame_buf.vline(x, y, self.gradient_height, color)
                hue += self.step
        if s:
            sat = 0
            y = self.s_start_height
            for x in range(
                self.gradient_left_start, self.gradient_left_start + self.gradient_width
            ):
                color = common.color565(*common.hsv_to_rgb(self.h, sat, 1))
                self.badge.screen.frame_buf.vline(x, y, self.gradient_height, color)
                sat += self.step
        if v:
            val_rgb = 0
            val_step = round(255 / self.gradient_width)
            # print(val_step)
            y = self.v_start_height
            for x in range(
                self.gradient_left_start, self.gradient_left_start + self.gradient_width
            ):
                # print(val_rgb)
                color = common.color565(val_rgb, val_rgb, val_rgb)
                # print(f"{color:016b}")
                self.badge.screen.frame_buf.vline(x, y, self.gradient_height, color)
                val_rgb = min(val_rgb + val_step, 255)

        # show a swatch
        self.badge.screen.frame_buf.rect(
            self.gradient_left_start + self.gradient_width + 20,
            self.h_start_height,
            self.ok_button_size,
            self.ok_button_size,
            common.color565(*common.hsv_to_rgb(self.h, self.s, self.v)),
            True,
        )
        # the actual OK button
        self.badge.screen.frame_buf.rect(
            self.ok_button_left,
            self.ok_button_top,
            self.ok_button_size,
            self.ok_button_size,
            self.badge.theme.bg2,
            True,
        )

        self.badge.screen.frame_buf.text(
            "OK",
            self.ok_button_left + self.ok_button_size // 2 - 8,
            self.ok_button_top + self.ok_button_size // 2 - 12,
            self.badge.theme.fg1,
        )

        self.badge.screen.frame_buf.text(
            "(A)",
            self.ok_button_left + self.ok_button_size // 2 - 12,
            self.ok_button_top + self.ok_button_size // 2 + 4,
            self.badge.theme.fg1,
        )

        self.badge.neopixels.fill(common.hsv_to_rgb(self.h, self.s, self.v))
        self.badge.screen.draw_frame()

    def set_color_from_touch(self, t):
        x, y = t
        if x > self.ok_button_left and x < self.ok_button_left + self.ok_button_size:
            if y > self.ok_button_top and y < self.ok_button_top + self.ok_button_size:
                self.selection_made = True
                return
        # be nice to the touch screen users and let them go off of either edge to select min and max
        if x < self.gradient_left_start:
            pos = 0
        elif x > self.gradient_left_start + self.gradient_width:
            pos = 1
        else:
            x -= self.gradient_left_start
            pos = x / (self.gradient_width)

        if y > self.h_start_height and y < self.h_start_height + self.gradient_height:
            self.h = pos
            self.focused_gradient = 0
            self.show(h=False, s=True, v=False)
        elif y > self.s_start_height and y < self.s_start_height + self.gradient_height:
            self.s = pos
            self.focused_gradient = 1
            self.show(h=False, s=False, v=False)
        elif y > self.v_start_height and y < self.v_start_height + self.gradient_height:
            self.v = pos
            self.focused_gradient = 2
            self.show(h=False, s=False, v=False)
        pass
