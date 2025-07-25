import time
import _thread
from lib.uwave import Wave_read
import gc
import board_config as bc

_MIDPOINT = 65536 // 2 - 1


class ShittyDAC:
    u8_frame_rate_adjustments = {
        ## these are pretty close to correct on my badge
        ## framerate: (playback_wait_us, playback_skip)
        8000: (103, 0),
        11_025: (70, 0),
        16_000: (41, 0),
        22_050: (24, 0),
        # technically 44100 kind of works but it sounds bad and takes up lots of space for no benefit
        # 44_100: (10, 0),
    }

    def __init__(self, badge, bufsize=4096, pwm_freq=300_000):
        self.badge = badge
        self.badge.speaker.pwm.freq(pwm_freq)
        self.bufsize = bufsize
        gc.collect()
        self.bufs = (bytearray(bufsize), bytearray(bufsize))
        self.playing_buf = 0
        self.file_done = False
        self.ready_to_fill = False
        self.ready_to_play = False
        self.cancel = False
        self.audio_file = None
        self.playback_wait_us = 0
        self.playback_skip = 0
        self.fill_buf_exited = False
        self.volume = 8
        self.total_buf_fills = None
        self.buf_fills = 0
        self.playhead_x = 0
        self.playhead_y = bc.SCREEN_HEIGHT - 5
        self.run_time_s = 0
        self.time_elapsed_s = 0
        self.time_elapsed_mins = 0
        self.paused = False

    def stop_playing(self):
        self.cancel = True

    def play_pause(self):
        self.paused = not self.paused

    def fill_buf(self):
        while (not self.file_done) and (not self.cancel):
            if self.ready_to_fill and not self.paused:
                next_playing_buf = (self.playing_buf + 1) % 2
                # print(f"filling {next_playing_buf}")
                self.ready_to_fill = False
                if self.audio_file.readinto(self.bufs[next_playing_buf]) <= 0:
                    self.file_done = True
                self.buf_fills += 1
                self.draw_progress()
                self.ready_to_play = True
        self.fill_buf_exited = True
        print("Done filling!")

    # it feels a little cursed to be doing this in the DAC class, but timing is tight enough that
    # it's got to happen wherever I can fit it in. I guess I could pass in a method from the GUI class that the DAC
    # calls and that would feel a little less cursed, but it would be doing the same thing
    def draw_progress(self):
        self.playhead_x = round(
            bc.SCREEN_WIDTH * (self.buf_fills / self.total_buf_fills)
        )
        self.badge.screen.fill_circle(
            self.playhead_x - 1, self.playhead_y, 4, self.badge.theme.fg2
        )
        self.badge.screen.fill_circle(
            self.playhead_x, self.playhead_y, 4, self.badge.theme.accent
        )
        self.time_elapsed_s = round(
            self.run_time_s * (self.buf_fills / self.total_buf_fills)
        )
        self.time_elapsed_mins = self.time_elapsed_s // 60
        self.time_elapsed_s %= 60
        self.badge.screen.frame_buf.rect(
            20, bc.SCREEN_HEIGHT - 40, 40, 8, self.badge.theme.bg2, True
        )
        self.badge.screen.frame_buf.text(
            f"{self.time_elapsed_mins:02}:{self.time_elapsed_s:02}",
            20,
            bc.SCREEN_HEIGHT - 40,
            self.badge.theme.fg1,
        )
        ## display playback delay for tuning
        # self.badge.screen.frame_buf.rect(
        #     100, bc.SCREEN_HEIGHT - 80, 24, 10, self.badge.theme.bg2, True
        # )
        # self.badge.screen.frame_buf.text(
        #     f"{self.playback_wait_us}",
        #     100,
        #     bc.SCREEN_HEIGHT - 80,
        #     self.badge.theme.fg1,
        # )
        self.badge.screen.draw_frame()

    def play_buf_8u(self):
        # print("playing 8u")
        p = self.playing_buf
        for i in range(0, self.bufsize, self.playback_skip + 1):
            # for sample in self.bufs[p]:
            self.badge.speaker.pwm.duty_u16(self.bufs[p][i] << self.volume)
            # print(f"waiting {self.playback_wait_us} us")
            time.sleep_us(self.playback_wait_us)
            # self.last_duty = self.bufs[p][i] << 8

    async def play_wav(self, filename):
        """
        Use a second thread and two buffers to load audio in the background while playing the current buffer
        """
        # get_wav_metadata can throw an error, but that is for the GUI to display a message and prevent actually calling this function
        # so the error shouldn't happen this time. Shouldn't...
        _, _, frame_rate, nframes = self.get_wav_metadata(filename)
        self.playback_wait_us, self.playback_skip = self.u8_frame_rate_adjustments[
            frame_rate
        ]
        self.run_time_s = nframes // frame_rate
        self.total_buf_fills = nframes // self.bufsize
        self.audio_file.seek(0x2C, 0)
        _thread.start_new_thread(self.fill_buf, ())
        # poor man's condition variables
        self.ready_to_fill = True
        while not self.ready_to_play:
            pass
        while (not self.file_done) and (not self.cancel):
            self.ready_to_fill = True
            # play_buf_fn()
            self.play_buf_8u()
            self.playing_buf = (self.playing_buf + 1) % 2
            # TODO if this is too slow, inline play_buf?
            # while this thread is playing audio, the second thread will fill up the other buffer and set playing_buf to point to it
            while (not self.ready_to_play or self.paused) and not self.cancel:
                pass
            self.ready_to_play = False
        print("Done playing!")
        while not self.fill_buf_exited:
            pass
        self.audio_file.close()
        self.reset()

    def reset(self):
        self.playing_buf = 0
        self.file_done = False
        self.ready_to_fill = False
        self.ready_to_play = False
        # TODO: hook up a button to set this to stop playing the file
        self.cancel = False
        self.audio_file = None
        self.playback_wait_us = 0
        self.playback_skip = 0
        # self.last_duty = 0
        self.fill_buf_exited = False
        self.total_buf_fills = None
        self.buf_fills = 0
        self.playhead_x = 0
        self.playhead_y = bc.SCREEN_HEIGHT - 5
        self.run_time_s = 0
        self.time_elapsed_s = 0
        self.time_elapsed_mins = 0
        self.paused = False
        for i in range(self.bufsize):
            self.bufs[0][i] = 0
            self.bufs[1][i] = 0

    def get_wav_metadata(self, filename):
        # get sample width, channels, and framerate for the wave file
        # throw errors if they can't be played
        self.audio_file = open(filename, "rb")
        w = Wave_read(self.audio_file)
        nchannels, sample_width, frame_rate, nframes, *_ = w.getparams()
        w.close()
        if sample_width != 1:
            self.reset()
            raise ValueError(
                f"Invalid sample width/bit depth: {sample_width}. Valid sample widths: 1 byte (8 bit unsigned)"
            )
        if nchannels != 1:
            self.reset()
            raise ValueError(f"Can't play stereo files (channels: {nchannels})")
        if frame_rate not in self.u8_frame_rate_adjustments.keys():
            self.reset()
            raise ValueError(
                f"Invalid frame rate/sample rate: {frame_rate}). Available framerates: {[r for r in self.u8_frame_rate_adjustments.keys()]}"
            )
        return (nchannels, sample_width, frame_rate, nframes)
