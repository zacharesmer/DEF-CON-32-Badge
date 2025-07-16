import board_config as bc
import asyncio
from machine import Pin


class Program:
    def __init__(self, badge):
        self.badge = badge
        self.badge.b_button.irq(self.exit_not_async, Pin.IRQ_FALLING)
        pass

    async def run(self):
        self.is_running = True
        from lib.common import lin_reg

        x_px = (40, 40, 280, 280)
        y_px = (40, 200, 40, 200)
        x_touches = []
        y_touches = []
        for i in range(len(x_px)):
            instructions = "Tap the circles to calibrate"
            self.badge.screen.text_in_box(
                instructions,
                0,
                0,
                self.badge.theme.fg1,
                self.badge.theme.bg2,
                box_width=320,
                box_height=240,
                fill=True,
            )
            self.badge.screen.fill_circle(x_px[i], y_px[i], 3, self.badge.theme.accent)
            self.badge.screen.draw_frame()
            await asyncio.sleep(0.5)
            touch = None
            while touch is None:
                if not self.is_running:
                    # bail out early if it's cancelled
                    return
                await asyncio.sleep(0)
                touch = self.badge.touch.get_one_touch()
            x_touches.append(touch[0])
            y_touches.append(touch[1])

        # print(f"x pixels: {x_px}")
        # print(f"x touches: {x_touches}")
        x_cal = lin_reg(x_px, x_touches)
        y_cal = lin_reg(y_px, y_touches)
        self.badge.touch.set_calibration(x_cal=x_cal, y_cal=y_cal)
        # todo: also update the preferences file
        prefs = self.badge.read_preferences()
        prefs["x_calibration"] = x_cal
        prefs["y_calibration"] = y_cal
        self.badge.write_preferences(prefs)
        await self.exit()

    def exit_not_async(self, arg):
        self.is_running = False

    async def exit(self):
        self.is_running = False
        print("exiting")
