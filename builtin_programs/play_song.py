from machine import Pin
from lib.dac import ShittyDAC


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
