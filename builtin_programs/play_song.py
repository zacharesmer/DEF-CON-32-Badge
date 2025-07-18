import board_config as bc
from machine import PWM, Pin
import time
import _thread


class ShittyDAC:
    def __init__(self, pwm, bufsize=4096, pwm_freq=500_000):
        self.pwm = pwm
        self.pwm.freq(pwm_freq)
        self.bufsize = bufsize
        self.bufs = (bytearray(bufsize), bytearray(bufsize))
        self.playing_buf = 0

        self.file_done = False
        self.ready_to_fill = True
        self.audio_file = None

    def fill_buf(self):
        # print("filling")
        self.ready_to_fill = False
        if self.audio_file.readinto(self.bufs[(self.playing_buf + 1) % 2]) <= 0:
            self.file_done = True
        self.ready_to_fill = True

    def play_buf(self):
        # print("playing")
        p = self.playing_buf
        for sample in self.bufs[p]:
            # for i in range(0, bufsize // 2, 2):
            self.pwm.duty_u16(sample << 8)
            # how to wait for 8 and a bit microseconds
            time.sleep_us(8)
            x = 1
            x = 2
            x = 3
            x = 4
            x = 5
            x = 6

    def play_raw_file(self, filename):
        self.audio_file = open(filename, "rb")
        self.fill_buf()
        # playing_buf = 1
        # fill_buf()
        # playing_buf = 0
        while not self.file_done:
            self.playing_buf = (self.playing_buf + 1) % 2
            _thread.start_new_thread(self.fill_buf, ())
            self.play_buf()
            # while not self.ready_to_fill:
            #     pass
            # plenty of time to update neopixels if you don't mind it sounding bad...
            # time.sleep_ms(1)

        self.audio_file.close()


class Program:
    def __init__(self, badge):
        self.badge = badge

        self.dac = ShittyDAC(badge.speaker.pwm)

    async def run(self):
        self.dac.play_raw_file("sd/astley.rawaudio")

    async def exit(self):
        print("lol you can't exit")
