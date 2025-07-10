import board_config as bc
import asyncio


class Program:
    def __init__(self, badge):
        self.badge = badge
        pass

    async def run(self):
        self.is_running = True
        from lib import lin_reg

        black = 0x0
        white = 0xFF_FF
        x_px = (20, 20, 300, 300)
        y_px = (20, 220, 20, 220)
        x_touches = []
        y_touches = []
        for i in range(len(x_px)):
            self.badge.screen.frame_buf.fill(black)
            instructions = "Tap the circles to calibrate"
            self.badge.screen.frame_buf.text(
                instructions,
                (bc.SCREEN_WIDTH // 2) - ((len(instructions) // 2) * 8),
                (bc.SCREEN_HEIGHT // 2) - (8 // 2),
                white,
            )
            self.badge.screen.fill_circle(x_px[i], y_px[i], 3, white)
            await asyncio.sleep(0.5)
            touch = None
            while touch is None:
                if not self.is_running:
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

    async def exit(self):
        self.is_running = False
        print("exiting")
