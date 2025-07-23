from lib.file_browser import FileBrowserProgram
from lib.dac import ShittyDAC
from machine import Pin
from lib.error_box import ErrorBox
import asyncio
import micropython

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
        self.badge.b_button.irq(self.stop_playing, Pin.IRQ_FALLING, hard=True)
        self.badge.up_button.irq(self.vol_up, Pin.IRQ_FALLING, hard=True)
        self.badge.down_button.irq(self.vol_down, Pin.IRQ_FALLING, hard=True)

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
            self.badge.screen.frame_buf.fill(self.badge.theme.bg2)
            self.badge.screen.frame_buf.text("Play?", 10, 10, self.badge.theme.fg1)
            self.badge.screen.draw_frame()
        else:
            super().show(refresh=refresh)

    async def play(self):
        self.setup_playback_buttons()
        try:
            self.dac.play_wav(self.open_filename)
        except ValueError as ve:
            eb = ErrorBox(self.badge, message=ve.value)
            eb.display_error()
        self.mode = "Directory"
        super().setup_buttons()
        # print(f"Done! {self.mode}")
        self.show()
