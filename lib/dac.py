import time
import _thread
from lib.uwave import Wave_read
import gc

_MIDPOINT = 65536 // 2 - 1


class ShittyDAC:
    u8_frame_rate_adjustments = {
        ## this does not reliably produce accurate speed
        ## but it works surprisingly well so hey whatever
        ## framerate: (playback_wait_us, playback_skip)
        8000: (110, 0),
        11_025: (80, 0),
        16_000: (50, 0),
        22_050: (28, 0),
        # technically this sort of works but it sounds bad and takes up lots of space for no benefit
        44_100: (5, 0),
    }

    def __init__(self, pwm, bufsize=4096, pwm_freq=300_000):
        self.pwm = pwm
        self.pwm.freq(pwm_freq)
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

    def stop_playing(self):
        self.cancel = True

    def fill_buf(self):
        while (not self.file_done) and (not self.cancel):
            if self.ready_to_fill:
                next_playing_buf = (self.playing_buf + 1) % 2
                # print(f"filling {next_playing_buf}")
                self.ready_to_fill = False
                if self.audio_file.readinto(self.bufs[next_playing_buf]) <= 0:
                    self.file_done = True
                self.ready_to_play = True
        self.fill_buf_exited = True
        print("Done filling!")

    def play_buf_8u(self):
        # print("playing 8u")
        p = self.playing_buf
        for i in range(0, self.bufsize, self.playback_skip + 1):
            # for sample in self.bufs[p]:
            self.pwm.duty_u16(self.bufs[p][i] << self.volume)
            # print(f"waiting {self.playback_wait_us} us")
            time.sleep_us(self.playback_wait_us)
            # self.last_duty = self.bufs[p][i] << 8

    async def play_wav(self, filename):
        """
        Use a second thread and two buffers to load audio in the background while playing the current buffer
        """
        # get_wav_metadata can throw an error, but that is for the GUI to display a message and prevent actually calling this function
        # so the error shouldn't happen this time. Shouldn't...
        _, _, frame_rate = self.get_wav_metadata(filename)
        self.playback_wait_us, self.playback_skip = self.u8_frame_rate_adjustments[
            frame_rate
        ]
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
            ## Note: this is just for debugging. The buffer needs to fill up faster than the audio plays or else it can't play in real time
            while not self.ready_to_play:
                print("uh oh couldn't load the buffer fast enough")
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
        for i in range(self.bufsize):
            self.bufs[0][i] = 0
            self.bufs[1][i] = 0

    def get_wav_metadata(self, filename):
        # get sample width, channels, and framerate for the wave file
        # throw errors if they can't be played
        self.audio_file = open(filename, "rb")
        w = Wave_read(self.audio_file)
        nchannels, sample_width, frame_rate, *_ = w.getparams()
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
        return (nchannels, sample_width, frame_rate)

    # def setup_wav_stuff(self, filename):
    #     # get metadata for the wave file
    #     self.audio_file = open(filename, "rb")
    #     w = Wave_read(self.audio_file)
    #     nchannels, sample_width, frame_rate, *_ = w.getparams()
    #     w.close()
    #     if sample_width != 1:
    #         self.reset()
    #         raise ValueError(
    #             f"Invalid sample width/bit depth: {sample_width}. Valid sample widths: 1 byte (8 bit unsigned)"
    #         )
    #     if nchannels != 1:
    #         self.reset()
    #         raise ValueError(f"Can't play stereo files (channels: {nchannels})")
    #     # scale the waiting time with frame rate. Higher framerate = wait less time
    #     # TODO: at lower frame rates there's a ton of time for something like neopixel animations...
    #     # Past some frame rate, set an amount of samples to skip because there will be a point where I can't handle them
    #     print(f"Getting adjustments for frame rate {frame_rate}")
    #     if sample_width == 1:
    #         adjustments = self.u8_frame_rate_adjustments.get(frame_rate)
    #     print(f"Adjsutments: {adjustments}")
    #     if adjustments is None:
    #         self.reset()
    #         raise ValueError(
    #             f"Invalid frame rate/sample rate: {frame_rate}). Available framerates: {[r for r in self.u8_frame_rate_adjustments.keys()]}"
    #         )
    #     else:
    #         self.playback_wait_us, self.playback_skip = adjustments
    #     print(f"Wave file metadata: {w.getparams()}")
    #     # wav data always starts at 0x2c, put the file pointer there
