from lib.file_browser import FileBrowserProgram
from lib.dac import ShittyDAC
from machine import Pin
from lib.error_box import ErrorBox
import asyncio
import micropython
import board_config as bc
from array import array

micropython.alloc_emergency_exception_buf(100)


class Program(FileBrowserProgram):
    def __init__(self, badge):
        super().__init__(
            badge, root_dir_name="music", file_extension="wav", create_file=False
        )
        self.dac = ShittyDAC(self.badge.speaker.pwm)

    def select(self, arg):
        # print(f"Selecting {self.current_selection}, mode: {self.mode}")
        # print(super())
        if self.mode == "File":
            asyncio.create_task(self.play())
        else:
            super().select(arg)

    def setup_playback_buttons(self):
        self.badge.a_button.irq(self.stop_playing, Pin.IRQ_FALLING, hard=True)
        self.badge.b_button.irq(self.stop_playing, Pin.IRQ_FALLING, hard=True)
        self.badge.up_button.irq(self.vol_up, Pin.IRQ_FALLING, hard=True)
        self.badge.down_button.irq(self.vol_down, Pin.IRQ_FALLING, hard=True)

    def un_setup_playback_buttons(self):
        self.badge.a_button.irq(None)
        self.badge.b_button.irq(None)
        self.badge.up_button.irq(None)
        self.badge.down_button.irq(None)

    def stop_playing(self, arg):
        self.dac.stop_playing()

    def vol_up(self, arg):
        if self.dac.volume < 8:
            self.dac.volume += 1

    def vol_down(self, arg):
        if self.dac.volume > 0:
            self.dac.volume -= 1

    def show(self, refresh=False):
        # print(f"Showing, mode is {self.mode}")
        if self.mode == "File":
            try:
                self.dac.get_wav_metadata(self.open_filename)
                self.badge.screen.frame_buf.fill(self.badge.theme.bg2)
                self.badge.screen.text_in_box(
                    f"Now playing: {self.open_filename}",
                    5,
                    5,
                    self.badge.theme.fg2,
                    self.badge.theme.accent,
                    text_width=bc.SCREEN_WIDTH - 20,
                    box_width=bc.SCREEN_WIDTH - 10,
                    box_height=40,
                )
                # self.badge.screen.frame_buf.text("Play?", 10, 10, self.badge.theme.fg1)
                triangle_width = 20
                triangle_height = 20
                triangle_points = array(
                    "h",
                    (0, 0, 0, triangle_height, triangle_width, triangle_height // 2),
                )
                self.badge.screen.frame_buf.poly(
                    bc.SCREEN_WIDTH // 2 - triangle_width // 2,
                    130,
                    triangle_points,
                    self.badge.theme.fg3,
                    True,
                )
                self.badge.screen.draw_frame()
            except ValueError as ve:
                asyncio.create_task(self.error(ve.value))
        elif self.mode == "Playing":
            self.badge.screen.frame_buf.fill(self.badge.theme.bg2)
            self.badge.screen.text_in_box(
                f"Now playing: {self.open_filename}",
                5,
                5,
                self.badge.theme.fg2,
                self.badge.theme.accent,
                text_width=bc.SCREEN_WIDTH - 20,
                box_width=bc.SCREEN_WIDTH - 10,
                box_height=40,
            )
            self.badge.screen.frame_buf.rect(
                bc.SCREEN_WIDTH // 2 - 10, 130, 20, 20, self.badge.theme.fg3, True
            )
            self.badge.screen.draw_frame()
        else:
            super().show(refresh=refresh)

    async def error(self, message):
        self.un_setup_playback_buttons()
        eb = ErrorBox(self.badge, message=message)
        eb.display_error()
        super().setup_buttons()
        self.mode = "Directory"
        self.show()

    async def play(self):
        self.mode = "Playing"
        self.show()
        self.setup_playback_buttons()
        await self.dac.play_wav(self.open_filename)
        self.mode = "Directory"
        super().setup_buttons()
        # print(f"Done! {self.mode}")
        self.show()
