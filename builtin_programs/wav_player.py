from lib.file_browser import FileBrowserProgram
from lib.dac import ShittyDAC
from machine import Pin
from lib.error_box import ErrorBox
import asyncio
import micropython
import board_config as bc
from array import array

micropython.alloc_emergency_exception_buf(500)


class Program(FileBrowserProgram):
    def __init__(self, badge):
        super().__init__(
            badge, root_dir_name="music", file_extension="wav", create_file=False
        )
        self.dac = ShittyDAC(self.badge)
        self.run_time_s = 0
        self.run_time_mins = 0
        # this is because in an actual hardware interrupt you can't directly schedule a bound method
        # https://docs.micropython.org/en/latest/reference/isr_rules.html#creation-of-python-objects
        self.draw_play_pause_ref = self.draw_play_pause

    def select(self, arg):
        # print(f"Selecting {self.current_selection}, mode: {self.mode}")
        # print(super())
        if self.mode == "File":
            asyncio.create_task(self.play())
        else:
            super().select(arg)

    def setup_playback_buttons(self):
        # need to set these differently for playback because it blocks the CPU so they
        # must be actual hardware interrupts
        super().un_setup_buttons()
        self.badge.a_button.irq(self.play_pause, Pin.IRQ_FALLING, hard=True)
        self.badge.b_button.irq(self.stop_playing, Pin.IRQ_FALLING, hard=True)
        self.badge.up_button.irq(self.vol_up, Pin.IRQ_FALLING, hard=True)
        self.badge.down_button.irq(self.vol_down, Pin.IRQ_FALLING, hard=True)

    def un_setup_playback_buttons(self):
        # the same buttons are all used in the parent class
        super().setup_buttons()

    def play_pause(self, arg):
        self.dac.play_pause()
        micropython.schedule(self.draw_play_pause_ref, True)

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
                _, _, frame_rate, nframes = self.dac.get_wav_metadata(
                    self.open_filename
                )
                self.run_time_s = nframes // frame_rate
                self.run_time_mins = self.run_time_s // 60
                self.run_time_s %= 60
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
                self.badge.screen.frame_buf.text(
                    f"00:00",
                    20,
                    bc.SCREEN_HEIGHT - 40,
                    self.badge.theme.fg1,
                )
                self.draw_play_pause()
                self.badge.screen.frame_buf.text(
                    f"{self.run_time_mins:02}:{self.run_time_s:02}",
                    bc.SCREEN_WIDTH - 60,
                    bc.SCREEN_HEIGHT - 40,
                    self.badge.theme.fg1,
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
            self.badge.screen.frame_buf.text(
                f"{self.run_time_mins:02}:{self.run_time_s:02}",
                bc.SCREEN_WIDTH - 60,
                bc.SCREEN_HEIGHT - 40,
                self.badge.theme.fg1,
            )
            self.draw_play_pause()
            self.badge.screen.draw_frame()
        else:
            super().show(refresh=refresh)

    def draw_play_pause(self, draw_screen=False):
        self.badge.screen.frame_buf.rect(
            bc.SCREEN_WIDTH // 2 - 10, 130, 20, 20, self.badge.theme.bg2, True
        )
        if self.dac.paused:
            self.badge.screen.frame_buf.rect(
                bc.SCREEN_WIDTH // 2 - 10, 130, 5, 20, self.badge.theme.fg3, True
            )
            self.badge.screen.frame_buf.rect(
                bc.SCREEN_WIDTH // 2 + 5, 130, 5, 20, self.badge.theme.fg3, True
            )
        else:
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
        if draw_screen:
            self.badge.screen.draw_frame()

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
        self.un_setup_playback_buttons()
        # print(f"Done! {self.mode}")
        self.show()
