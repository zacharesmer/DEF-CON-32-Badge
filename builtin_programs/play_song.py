import board_config as bc
from machine import PWM, Pin
import time
import _thread
import asyncio
from uwave import Wave_read
import struct


_MIDPOINT = 65536 // 2 - 1


class ShittyDAC:
    frame_rate_adjustments = {
        # (playback_wait_us, playback_skip)
        8000: (25, 0),
        11_025: (60, 0),
        16_000: (15, 0),
        22_050: (9, 0),
        44_100: (0, 0),
    }

    def __init__(self, pwm, bufsize=4096, pwm_freq=500_000):
        self.pwm = pwm
        self.pwm.freq(pwm_freq)
        self.bufsize = bufsize
        self.bufs = (bytearray(bufsize), bytearray(bufsize))
        self.playing_buf = 0
        self.file_done = False
        self.ready_to_fill = False
        self.ready_to_play = False
        # TODO: hook up a button to set this to stop playing the file
        self.cancel = False
        self.audio_file = None
        self.playback_wait_us = 0
        self.playback_skip = 0

    def fill_buf(self):
        print("filling")
        while (not self.file_done) and (not self.cancel):
            if self.ready_to_fill:
                self.ready_to_fill = False
                next_playing_buf = (self.playing_buf + 1) % 2
                if self.audio_file.readinto(self.bufs[next_playing_buf]) <= 0:
                    self.file_done = True
                # by this point, hopefully self.playing buf should already have been read by play_buf and we can change it?
                # if this explodes I can move it back on the main thread but I'd rather not
                # self.playing_buf = next_playing_buf
                self.ready_to_play = True

    def play_buf_16s(self):
        print("playing 16s")
        p = self.playing_buf
        # for sample in self.bufs[p]:
        for i in range(0, self.bufsize, 2 + self.playback_skip):
            # we've got 16 bit signed data, so we need to add 32,767 to map to valid PWM values
            # and it's little endian so I've got to flip it
            # clearly the wav standard designers did not mean for the data to be used in this way
            self.pwm.duty_u16(
                struct.unpack("<h", self.bufs[p][i : i + 2])[0] + _MIDPOINT
            )
            time.sleep_us(self.playback_wait_us)
            # x = 1
            # x = 2
            # x = 3
            # x = 4
            # x = 5
            # x = 6

    def play_buf_8u(self):
        print("playing 8u")
        p = self.playing_buf
        for i in range(0, self.bufsize, self.playback_skip + 1):
            # for sample in self.bufs[p]:
            self.pwm.duty_u16(self.bufs[p][i] << 8)
            time.sleep_us(self.playback_wait_us)
            # x = 1
            # x = 2
            # x = 3
            # x = 4
            # x = 5
            # x = 6

    def play_wav(self, filename):
        """
        Use a second thread and two buffers to load audio in the background while playing out of the current buffer
        """
        # get metadata for the wave file
        self.audio_file = open(filename, "rb")
        w = Wave_read(self.audio_file)
        nchannels, sample_width, frame_rate, *_ = w.getparams()
        w.close()
        # adjust the playback settings based on the metadata
        # need different functions to handle different sample width/bit depth
        if sample_width == 1:
            play_buf_fn = self.play_buf_8u
        elif sample_width == 2:
            play_buf_fn = self.play_buf_16s
        else:
            print(f"Invalid sample width/bit depth: {sample_width}")
            print("Valid sample widths: 1 (8 bit unsigned), 2 (16 bit signed)")
            return
        if nchannels != 1:
            print(f"Can't play stereo files (channels: {nchannels})")
        # scale the waiting time with frame rate, somehow. Higher framerate = wait less
        # Also past some frame rate tbd, set an amount of samples to skip because there will be a point where I can't handle them
        # it may have to be different for 8 and 16 bit depths
        adjustments = self.frame_rate_adjustments.get(frame_rate)
        if adjustments is None:
            print(f"Invalid frame rate/sample rate: {frame_rate}")
            print(
                f"Available framerates: {[r for r in self.frame_rate_adjustments.keys()]}"
            )
        else:
            self.playback_wait_us, self.playback_skip_frames = adjustments
        print(f"Wave file metadata: {w.getparams()}")
        # wav data always starts at 0x2c, put the file there
        self.audio_file.seek(0x2C, 0)
        _thread.start_new_thread(self.fill_buf, ())
        # poor man's condition variables
        self.ready_to_fill = True
        while not self.ready_to_play:
            pass
        while (not self.file_done) and (not self.cancel):
            self.ready_to_fill = True
            self.playing_buf = (self.playing_buf + 1) % 2
            play_buf_fn()
            # TODO if this is too slow, extract and duplicate part of this function and inline the two play_bufs
            # while it's playing, the second thread will fill up the other buffer and set playing_buf to point to it
            # TODO: after the timing is sorted out remove this "condition variable" for performance
            while not self.ready_to_play:
                print("uh oh couldn't load the buffer fast enough")
            self.ready_to_play = False
        self.audio_file.close()


class Program:
    def __init__(self, badge):
        self.badge = badge
        self.dac = ShittyDAC(badge.speaker.pwm)

    async def run(self):
        self.dac.play_wav("boing_x.wav")
        # self.dac.play_wav("sd/rickroll.wav")

    async def exit(self):
        # print("lol you can't exit")
        self.dac.cancel = True


# from badge import DC32_Badge

# b = DC32_Badge()
# p = Program(b)
# asyncio.run(p.run())
