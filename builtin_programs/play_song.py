import board_config as bc
from machine import PWM, Pin
import time
import _thread
from uwave import Wave_read

# import struct


_MIDPOINT = 65536 // 2 - 1


class ShittyDAC:
    u8_frame_rate_adjustments = {
        ## this does not reliably produce accurate speed
        ## but it works surprisingly well so hey whatever
        ## (playback_wait_us, playback_skip)
        8000: (110, 0),
        11_025: (80, 0),
        16_000: (50, 0),
        22_050: (30, 0),
        # technically this sort of works but it sounds bad and takes up lots of space for no benefit
        44_100: (5, 0),
    }
    # # look don't try to play 16 bit audio on this thing there's no point
    # # I implemented it for compatibility since it's a common format but it just sounds like garbage and takes up so much space
    # s16_frame_rate_adjustments = {
    #     # (playback_wait_us, playback_skip)
    #     8000: (25, 0),
    #     11_025: (20, 0),
    #     16_000: (15, 0),
    #     22_050: (40, 2),
    #     44_100: (0, 2),
    # }

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
        # self.last_duty = 0

    def fill_buf(self):
        while (not self.file_done) and (not self.cancel):
            if self.ready_to_fill:
                # print("filling")
                self.ready_to_fill = False
                next_playing_buf = (self.playing_buf + 1) % 2
                if self.audio_file.readinto(self.bufs[next_playing_buf]) <= 0:
                    self.file_done = True
                # by this point, hopefully self.playing buf should already have been read by play_buf and we can change it?
                # if this explodes I can move it back on the main thread but I'd rather not
                # self.playing_buf = next_playing_buf
                self.ready_to_play = True

    # def play_buf_16s(self):
    #     """
    #     Provided for anyone's curiosity, but it sounds bad and there's no point
    #     """
    #     # print("playing 16s")
    #     p = self.playing_buf
    #     # for sample in self.bufs[p]:
    #     i = 0
    #     for i in range(0, self.bufsize, 2 + self.playback_skip):
    #         # we've got 16 bit signed data, so we need to add 32,767 (the max negative value) to
    #         # map to valid PWM values (0 to 65536)
    #         # and it's little endian so I've got to flip it
    #         # clearly the wav standard designers did not mean for the data to be used in this way
    #         self.pwm.duty_u16(
    #             struct.unpack("<h", self.bufs[p][i : i + 2])[0] + _MIDPOINT
    #         )
    #         time.sleep_us(self.playback_wait_us)

    def play_buf_8u(self):
        # print("playing 8u")
        p = self.playing_buf
        for i in range(0, self.bufsize, self.playback_skip + 1):
            # for sample in self.bufs[p]:
            self.pwm.duty_u16(self.bufs[p][i] << 8)
            # print(f"waiting {self.playback_wait_us} us")
            time.sleep_us(self.playback_wait_us)
            # self.last_duty = self.bufs[p][i] << 8

    def play_wav(self, filename):
        """
        Use a second thread and two buffers to load audio in the background while playing the current buffer
        """
        self.setup_wav_stuff(filename)
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
            # TODO if this is too slow, inline play_buf
            # while this thread is playing audio, the second thread will fill up the other buffer and set playing_buf to point to it
            ## Note: this is just for debugging. The buffer needs to fill up faster than the audio plays or else it can't play in real time
            while not self.ready_to_play:
                print("uh oh couldn't load the buffer fast enough")
            self.ready_to_play = False
        self.audio_file.close()

    def setup_wav_stuff(self, filename):
        # get metadata for the wave file
        self.audio_file = open(filename, "rb")
        w = Wave_read(self.audio_file)
        nchannels, sample_width, frame_rate, *_ = w.getparams()
        w.close()
        # # adjust the playback settings based on the metadata
        # # need different functions to handle different sample width/bit depth
        # if sample_width == 1:
        #     play_buf_fn = self.play_buf_8u
        # # elif sample_width == 2:
        # #     play_buf_fn = self.play_buf_16s
        if sample_width != 1:
            print(f"Invalid sample width/bit depth: {sample_width}")
            print("Valid sample widths: 1 (8 bit unsigned)")
            return
        if nchannels != 1:
            print(f"Can't play stereo files (channels: {nchannels})")
            return
        # scale the waiting time with frame rate. Higher framerate = wait less time
        # TODO: at lower frame rates there's a ton of time for something like neopixel animations...
        # Past some frame rate tbd, set an amount of samples to skip because there will be a point where I can't handle them
        # it may have to be different for 8 and 16 bit depths
        print(f"Getting adjustments for frame rate {frame_rate}")
        if sample_width == 1:
            adjustments = self.u8_frame_rate_adjustments.get(frame_rate)
        # elif sample_width == 2:
        #     adjustments = self.s16_frame_rate_adjustments.get(frame_rate)
        print(f"Adjsutments: {adjustments}")
        if adjustments is None:
            print(f"Invalid frame rate/sample rate: {frame_rate}")
            print(
                f"Available framerates: {[r for r in self.u8_frame_rate_adjustments.keys()]}"
            )
            return
        else:
            self.playback_wait_us, self.playback_skip = adjustments
        print(f"Wave file metadata: {w.getparams()}")
        # wav data always starts at 0x2c, put the file there
        self.audio_file.seek(0x2C, 0)


class Program:
    def __init__(self, badge):
        self.badge = badge
        self.dac = ShittyDAC(badge.speaker.pwm)

    def stop_playing(self, arg):
        self.dac.cancel = True

    async def run(self):
        self.badge.b_button.irq(self.stop_playing, Pin.IRQ_FALLING, hard=True)
        self.dac.play_wav("sd/Music/Game music/Final_Boss-22050-u8.wav")
        # self.dac.play_wav("sd/Music/astley-8000-u8.wav")
        # self.dac.play_wav("sd/Music/astley-22050-u8.wav")
        # self.dac.play_wav("sd/Music/bach-22050-u8.wav")
        # self.dac.play_wav("sd/Music/astley-8000-u8.wav")
        # self.dac.play_wav("sd/Music/astley-44100-u8.wav")

    async def exit(self):
        # print("lol you can't exit")
        self.stop_playing(None)


# from badge import DC32_Badge

# b = DC32_Badge()
# p = Program(b)
# asyncio.run(p.run())
