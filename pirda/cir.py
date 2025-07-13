from pirda.cir_generated import cir_rx
import rp2
from machine import Pin, PWM, Timer
import board_config as bc
import time
import asyncio
from array import array

import micropython

micropython.alloc_emergency_exception_buf(100)


class CIR:
    def __init__(self, rx_pin_num=bc.IRDA_RX_PIN, tx_pin_num=bc.IRDA_TX_PIN):
        pio = rp2.PIO(bc.CIR_PIO)
        rx_pin = Pin(rx_pin_num, Pin.IN, pull=Pin.PULL_UP)
        # if there are some really long remote signals out there this could be increased
        self.rx_timings = array("I", [0 for _ in range(1024)])
        # in or maybe jmp pin is used for the wait instruction
        # out pin is used for the mov instruction (sampling)
        self.rx_machine = pio.state_machine(
            bc.CIR_RX_SM,
            cir_rx,
            freq=19_000_000,
            in_base=rx_pin,
            out_base=rx_pin,
            jmp_pin=rx_pin,
        )
        self.rx_machine.active(False)

        self.tx_pwm = PWM(Pin(tx_pin_num, mode=Pin.OUT), freq=38_000, duty_u16=0)
        # duty cycle of .33
        self.tx_on_duty = 21842
        # .5
        self.tx_on_duty = 32768
        # .66
        self.tx_on_duty = 43684
        self.tx_off_duty = 0
        # self.tx_on = True
        self.cancel = False
        self.started_receiving = False

    def start_receiving(self):
        self.count = 0
        self.last = time.ticks_us()
        self.new = None
        self.falling = False
        for i in range(len(self.rx_timings)):
            self.rx_timings[i] = 0
        self.rx_machine.irq(self.signal_edge_handler, hard=True)
        self.rx_machine.restart()
        self.rx_machine.active(True)

    def stop_receiving(self):
        self.rx_machine.irq(None)
        self.rx_machine.active(False)

    # strip off the first timing since it's garbage and then end at the first 0
    def get_rx_timings(self):
        end = 0
        for i, t in enumerate(self.rx_timings):
            if t == 0:
                end = i
                break
        return self.rx_timings[1:end]

    def send_timings(self, timings):
        on = True
        # self.tx_timings = timings
        for t in timings:
            if on:
                self.tx_pwm.duty_u16(self.tx_on_duty)
            else:
                self.tx_pwm.duty_u16(self.tx_off_duty)
            on = not on
            time.sleep_us(t)
        self.tx_pwm.duty_u16(self.tx_off_duty)

    async def receive_one_signal(self, timeout_us=150_000):
        self.cancel = False
        self.started_receiving = False
        while not self.cancel:
            if (
                self.started_receiving
                and time.ticks_diff(time.ticks_us, self.last) > timeout_us
            ):
                break
            await asyncio.sleep()

    def signal_edge_handler(self, arg):
        self.started_receiving = True
        self.new = time.ticks_us()
        # the falling edge interrupt may happen up to ~26 us late depending when on how the sampling window lined up
        # this adjustmest is so it will be off by at most +/= half of that
        if self.falling:
            self.new -= 13
        self.falling = not self.falling
        self.rx_timings[self.count] = time.ticks_diff(self.new, self.last)
        self.last = self.new
        self.count += 1
