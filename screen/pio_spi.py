"""
The badge doesn't have the screen hooked up to a hardware SPI, so we've got to do it with PIO
"""

from machine import Pin
import rp2
import board_config


@rp2.asm_pio(
    out_init=(rp2.PIO.OUT_HIGH,),
    # out_shiftdir=rp2.PIO.SHIFT_RIGHT,
    sideset_init=(rp2.PIO.OUT_HIGH,),
    autopull=True,
    pull_thresh=8,
    fifo_join=rp2.PIO.JOIN_TX,
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
)
def pio_spi():
    wrap_target()
    out(pins, 1).side(0x0)
    nop().side(0x1)
    wrap()
    # there's no miso, so this is literally it


class PIO_SPI:
    def __init__(
        self,
        baudrate=62_500_000,
        sck=board_config._DISPLAY_SCK_PIN,
        mosi=board_config._DISPLAY_DO_PIN,
    ):

        lcd_mosi = Pin(mosi, mode=Pin.OUT)
        lcd_mosi.on()

        lcd_clk_pin = Pin(sck, mode=Pin.OUT)
        lcd_clk_pin.on()

        pio = rp2.PIO(board_config._DISPLAY_PIO)

        self.display_machine = pio.state_machine(
            board_config._DISPLAY_SM,
            pio_spi,
            freq=baudrate * 2,
            out_base=lcd_mosi,
            sideset_base=lcd_clk_pin,
        )
        self.display_machine.active(True)

    def write(self, data):
        for byte in data:
            # print(f"writing {byte:08b}")
            # print(self.display_machine.tx_fifo())
            self.display_machine.put(byte << 24)
