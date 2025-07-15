"""
Heavily based on Pico Examples: https://github.com/raspberrypi/pico-examples

Copyright 2020 (c) 2020 Raspberry Pi (Trading) Ltd.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
   disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

import array
from machine import Pin, mem32
import rp2
import board_config as bc
import uctypes

# from ws2812_generated import ws2812_pio


class WS2812:
    def __init__(
        self,
        num_leds=bc.NEOPIXEL_NUM_LEDS,
        pin=bc.NEOPIXEL_PIN,
        pio_index=bc.NEOPIXEL_PIO,
        sm_index=bc.NEOPIXEL_SM,
        auto_write=False,
    ):
        self.num_leds = num_leds
        pio = rp2.PIO(pio_index)
        # Create the StateMachine with the ws2812 program, outputting on Pin(22).
        self.neopixel_machine = pio.state_machine(
            sm_index, ws2812_pio, freq=8_000_000, sideset_base=Pin(pin)
        )
        # Start the StateMachine, it will wait for data on its FIFO.
        self.neopixel_machine.active(True)
        self.pixels = array.array("I", [0 for _ in range(num_leds)])
        # self.neopixel_machine.put(self.pixels[0] << 24)
        self.write()
        if auto_write:
            self._start_auto_write()

    def __setitem__(self, index, val):
        r, g, b = val
        self.pixels[index] = ((r & 0xFF) << 16) | ((g & 0xFF) << 24) | ((b & 0xFF) << 8)

    def __getitem__(self, index):
        r = (self.pixels[index] >> 16) & 0xFF
        g = (self.pixels[index] >> 24) & 0xFF
        b = (self.pixels[index] >> 8) & 0xFF
        return (r, g, b)

    def __len__(self):
        return self.num_leds

    def fill(self, value):
        for p in range(self.num_leds):
            self[p] = value

    def write(self):
        for p in self.pixels:
            self.neopixel_machine.put(p)

    def _start_auto_write(self, nop_pio_index=bc.NOP_PIO, nop_sm=bc.NOP_SM):
        pio = rp2.PIO(nop_pio_index)
        # one cycle of 16,000 Hz is 62.55 micro seconds.
        self.nop_pio = pio.state_machine(nop_sm, nop_pio, freq=16_000)
        self.nop_pio.active(True)
        # self.time_dma = time.time_ns()
        self.dma1 = rp2.DMA()
        self.dma2 = rp2.DMA()
        self.dma3 = rp2.DMA()

        mem32[bc.DISPLAY_DMA_ABORT_ADDRESS] = (0x1 << self.dma1.channel) | (
            0x1 << self.dma3.channel
        )  # aborting DMA channels seems to help restart DMA without a full power cycle? idk actually
        while mem32[bc.DISPLAY_DMA_ABORT_ADDRESS] != 0:
            continue
        # make a buffer with the data that dma3 will read from to update the config of dma1
        self.dma1_read_start = array.array("I", [uctypes.addressof(self.pixels)])
        self.dma1_ctrl = self.dma1.pack_ctrl(
            size=2,  # 4 byte/1 word chunks
            # size=0,
            inc_write=False,
            irq_quiet=True,
            chain_to=self.dma2.channel,
            treq_sel=bc.NEOPIXEL_REQ_SEL,
            # bswap=True,
        )
        self.dma1.config(
            # read=self.pixels,
            write=self.neopixel_machine,
            count=self.num_leds,
            ctrl=self.dma1_ctrl,
            trigger=False,
        )
        # self.dma1.irq(self.dma1_irq)
        # this just exists to do absolutely nothing for 50 microseconds to pause before sending the next round of data
        self.dma2_ctrl = self.dma2.pack_ctrl(
            size=0,
            inc_read=False,
            inc_write=False,
            irq_quiet=True,
            chain_to=self.dma3.channel,
            treq_sel=bc.NOP_REQ_SEL,
        )
        self.dma2.config(
            read=self.pixels,  # this does not matter it could read literally any data
            write=self.nop_pio,  # this PIO just runs slowly, pulls some data, and does nothing with it
            count=10,  # do I need to send multiple things so it will actually wait a cycle? i think so
            ctrl=self.dma2_ctrl,
            trigger=False,
        )
        # self.dma2.irq(self.dma2_irq)
        self.dma3_ctrl = self.dma3.pack_ctrl(
            size=2,  # transfer 32 bit words for registers
            inc_read=False,  # always transfer the same thing to the same place
            inc_write=False,
            irq_quiet=False,
            # don't need to chain because this one writes to a trigger register
        )
        dma_regs_start = 0x50000000
        AL3_READ_ADDR_TRIG_OFFSET = 0x03C
        self.dma3.config(
            read=self.dma1_read_start,
            # tried it the recommended way but it didn't work, maybe an rp2040/2350 difference?
            # write=self.dma1.registers[15],
            write=dma_regs_start
            + dma_regs_offset(self.dma1.channel)
            + AL3_READ_ADDR_TRIG_OFFSET,
            count=1,
            ctrl=self.dma3_ctrl,
            trigger=False,
        )
        # and we're off!
        self.dma3.active(True)


@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True,
    pull_thresh=24,
    fifo_join=rp2.PIO.JOIN_TX,
)
def ws2812_pio():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1).side(0)[T3 - 1]
    jmp(not_x, "do_zero").side(1)[T1 - 1]
    jmp("bitloop").side(1)[T2 - 1]
    label("do_zero")
    nop().side(0)[T2 - 1]
    wrap()


@rp2.asm_pio(fifo_join=rp2.PIO.JOIN_TX)
def nop_pio():
    pull(block)


def dma_regs_offset(which_dma):
    return which_dma * 0x40
