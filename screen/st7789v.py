"""
Screen driver to hold RGB565 pixels in a framebuf and use DMA to push them out over SPI to the TFT LCD XYZ LMNOPQRSTUV

Heavily based on github.com/russhughes/st7789py_mpy but also pretty much entirely rewritten

"""

import framebuf
import board_config as bc
from screen.pio_spi import PIO_SPI
from machine import Pin, mem32
import time
import rp2
import screen.st7789v_definitions as defs
import uctypes
import struct
import array
from lib import color565, shitty_wrap_text
from math import floor


class ST7789V:
    def __init__(
        self,
        cs=bc.DISPLAY_CS_PIN,
        dc=bc.DISPLAY_DC_PIN,
        clk=bc.DISPLAY_SCK_PIN,
        mosi=bc.DISPLAY_DO_PIN,
        backlight=bc.DISPLAY_BL_PIN,
        manual_draw=False,
    ):
        #
        self.frame_buf_bytes = bc.SCREEN_HEIGHT * bc.SCREEN_WIDTH * 2
        buf = bytearray(self.frame_buf_bytes)
        self.frame_buf = framebuf.FrameBuffer(
            buf, bc.SCREEN_WIDTH, bc.SCREEN_HEIGHT, framebuf.RGB565
        )
        self.frame_buf.fill(defs.BLACK)

        self.spi = PIO_SPI(sck=clk, mosi=mosi)

        self.cs = Pin(cs, Pin.OUT)
        self.dc = Pin(dc, Pin.OUT)
        self.backlight = Pin(backlight, Pin.OUT)

        self.setup_display()
        if manual_draw:
            self.setup_DMA()
            self.draw_frame()
        # kick off DMA to refresh the display autonomously
        else:
            self.setup_DMA_pingpong()

    def setup_display(self):
        for cmd, data, delay in defs._ST7789_INIT_CMDS:
            self.send_command(cmd)
            self.send_argument(data)
            time.sleep_ms(delay)
        self.backlight.on()

    def setup_DMA_pingpong(self):
        self.dma1 = rp2.DMA()
        # so named because I thought I also needed dma2 to reset the count, but apparently that's not true
        self.dma3 = rp2.DMA()

        # aborting all DMA channels may help restart DMA without a full power cycle?
        # TODO: this doesn't seem to be working
        mem32[bc.DISPLAY_DMA_ABORT_ADDRESS] = (0x1 << self.dma1.channel) | (
            0x1 << self.dma3.channel
        )
        while mem32[bc.DISPLAY_DMA_ABORT_ADDRESS] != 0:
            continue
        # make a buffer with the data that dma3 will read from to update the config of dma1
        # self.dma1_count = array.array("I", [self.frame_buf_bytes])
        self.dma1_read_start = array.array("I", [uctypes.addressof(self.frame_buf)])
        self.dma1_ctrl = self.dma1.pack_ctrl(
            size=0,  # send 1 byte at a time to SPI
            inc_write=False,
            irq_quiet=True,
            chain_to=self.dma3.channel,
            treq_sel=bc.DISPLAY_REQ_SEL,
            bswap=True,
        )
        self.dma1.config(
            read=self.frame_buf,
            write=self.spi.display_machine,
            count=self.frame_buf_bytes,
            ctrl=self.dma1_ctrl,
            trigger=False,
        )
        self.dma3_ctrl = self.dma3.pack_ctrl(
            size=2,  # transfer 32 bit words for registers
            inc_read=False,  # always transfer the same thing to the same place
            inc_write=False,
            irq_quiet=True,
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

        self.send_command(defs._ST7789_RAMWR)
        self.send_argument(
            b"\x00"
        )  # need to send 1 byte of nothing so the 2 byte colors are offset correctly, LMAO
        self.cs.off()
        # aaaaand we're off!
        self.dma3.active(True)

    def setup_DMA(self):
        mem32[bc.DISPLAY_DMA_ABORT_ADDRESS] = (
            0x1  # aborting the channel seems to help restart DMA without a full power cycle
        )
        while mem32[bc.DISPLAY_DMA_ABORT_ADDRESS] != 0:
            continue
        self.dma1 = rp2.DMA()
        self.dma1_ctrl = self.dma1.pack_ctrl(
            size=0,
            inc_write=False,
            irq_quiet=False,
            # chain_to=self.dma2.channel,
            treq_sel=bc.DISPLAY_REQ_SEL,
            bswap=True,
        )

    # use this method to manually trigger a redraw if that's how your program is set up
    # this can be attached to an interrupt that fires every time the screen finishes drawing
    def draw_frame(self, *args):
        self.cs.off()
        # Put the next pixel at the beginning of the screen's display RAM
        self.send_command(defs._ST7789_RAMWR)
        self.send_argument(
            b"\x00"
        )  # need to send 1 byte of nothing so the 2 byte colors are offset correctly, LMAO
        self.cs.off()
        self.dma1.config(
            read=self.frame_buf,
            write=self.spi.display_machine,
            count=self.frame_buf_bytes,
            ctrl=self.dma1_ctrl,
            trigger=True,
        )
        # self.cs.on()

    def send_command(self, cmd):
        # print(f"Sending {cmd}")
        self.cs.off()
        self.dc.off()
        self.spi.write(cmd)
        self.dc.on()
        self.cs.on()
        # pass

    def send_argument(self, data):
        # print(f"Sending {data}")

        self.cs.off()
        self.dc.on()  # just in case
        self.spi.write(data)
        self.cs.on()

    # these are just convenience methods so I could test with the same API in the other driver, they basically forward arguments to the framebuf
    def fill(self, color):
        self.frame_buf.fill(color)
        # self.frame_buf.text("???", 10, 10, MAGENTA)

    def fill_circle(self, x, y, r, color):
        self.frame_buf.ellipse(x, y, r, r, color, True)

    def pixel(self, x, y, color):
        self.frame_buf.pixel(x, y, color)

    def text_in_box(
        self,
        text,
        x,
        y,
        text_color,
        box_color,
        text_width=None,
        box_width=None,
        box_height=None,
        fill=False,
        line_height=15,
    ):
        """
        If text_width is provided, (shittily) wrap the text
        Center the text in the box, or if it's too long just start at the top and overflow out the bottom
        """
        if text_width is None:
            if box_width is None:
                text_width = len(text * 8)
            else:
                text_width = min(box_width, len(text) * 8)

        wrapped = shitty_wrap_text(text, floor(text_width / 8))

        total_text_height = line_height * len(wrapped) - (line_height - 8)
        box_height = total_text_height + 2 if box_height is None else box_height
        box_width = text_width + 2 if box_width is None else box_width
        self.frame_buf.rect(x, y, box_width, box_height, box_color, fill)
        text_x = x + (box_width - text_width) // 2
        if total_text_height < box_height:
            text_y = y + (box_height - total_text_height) // 2
        else:
            text_y = y + 1
        for line in wrapped:
            self.frame_buf.text(line, text_x, text_y, text_color)
            text_y += line_height


def dma_regs_offset(which_dma):
    return which_dma * 0x40
