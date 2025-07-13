""" """

import lib
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

    async def get_color(self):
        self.setup_buttons()
        self.badge.screen.fill(bg_color)
        self.show()
        self.is_running = True
        while self.is_running:
            t = self.badge.touch.get_one_touch_in_pixels()
            if t is not None:
                self.set_color_from_touch(t)
            if self.selection_made:
                return lib.hsv_to_rgb(self.h, self.s, self.v)

    def show(self, h=True, s=True, v=True):
        # draw outlines and a little indicator of the current selections
        for i, start_height in enumerate(
            (self.h_start_height, self.s_start_height, self.v_start_height)
        ):
            if i == self.focused_gradient:
                color = accent_color
            else:
                color = bg_color
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
            bg_color,
            True,
        )
        self.badge.screen.frame_buf.text(
            "^",
            self.gradient_left_start + round(self.h * self.gradient_width) - 4,
            self.h_start_height + self.gradient_height + 1,
            accent_color,
        )
        # s indicator
        self.badge.screen.frame_buf.rect(
            self.gradient_left_start - 5,
            self.s_start_height + self.gradient_height + 1,
            self.gradient_width + 10,
            10,
            bg_color,
            True,
        )
        self.badge.screen.frame_buf.text(
            "^",
            self.gradient_left_start + round(self.s * self.gradient_width) - 4,
            self.s_start_height + self.gradient_height + 1,
            accent_color,
        )
        # v indicator
        self.badge.screen.frame_buf.rect(
            self.gradient_left_start - 5,
            self.v_start_height + self.gradient_height + 1,
            self.gradient_width + 10,
            10,
            bg_color,
            True,
        )
        self.badge.screen.frame_buf.text(
            "^",
            self.gradient_left_start + round(self.v * self.gradient_width) - 4,
            self.v_start_height + self.gradient_height + 1,
            accent_color,
        )

        # draw H S V gradients
        if h:
            hue = 0
            y = self.h_start_height
            for x in range(
                self.gradient_left_start, self.gradient_left_start + self.gradient_width
            ):
                color = lib.color565(*lib.hsv_to_rgb(hue, 1, 1))
                self.badge.screen.frame_buf.vline(x, y, self.gradient_height, color)
                hue += self.step
        if s:
            sat = 0
            y = self.s_start_height
            for x in range(
                self.gradient_left_start, self.gradient_left_start + self.gradient_width
            ):
                color = lib.color565(*lib.hsv_to_rgb(self.h, sat, 1))
                self.badge.screen.frame_buf.vline(x, y, self.gradient_height, color)
                sat += self.step
        if v:
            val_rgb = 0
            val_step = round(255 / self.gradient_width)
            print(val_step)
            y = self.v_start_height
            for x in range(
                self.gradient_left_start, self.gradient_left_start + self.gradient_width
            ):
                # print(val_rgb)
                color = lib.color565(val_rgb, val_rgb, val_rgb)
                # print(f"{color:016b}")
                self.badge.screen.frame_buf.vline(x, y, self.gradient_height, color)
                val_rgb = min(val_rgb + val_step, 255)

        self.badge.screen.frame_buf.rect(
            self.gradient_left_start + self.gradient_width + 20,
            self.h_start_height,
            50,
            self.gradient_height,
            lib.color565(*lib.hsv_to_rgb(self.h, self.s, self.v)),
            True,
        )

        self.badge.screen.frame_buf.text(
            "Press A",
            self.gradient_left_start + self.gradient_width + 10,
            self.s_start_height,
            fg_color,
        )
        self.badge.screen.frame_buf.text(
            "to select",
            self.gradient_left_start + self.gradient_width + 10,
            self.s_start_height + 15,
            fg_color,
        )

        self.badge.neopixels.fill(lib.hsv_to_rgb(self.h, self.s, self.v))

    def set_color_from_touch(self, t):
        # could maybe cheat here and just see what color the pixel is in the frame buf?
        x, y = t

        # be nice to the touch screen users and let them go off of either edge and select red
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


fg_color = 0xFF_FF
accent_color = 0xFF_FF
bg_color = 0x0
