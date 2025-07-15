"""
Adapted from the board definition in pico SDK: https://github.com/raspberrypi/pico-sdk/blob/master/src/boards/include/boards/defcon32_badge.h

do the consts help? hopefully at least a bit
"""

from micropython import const

DISPLAY_DC_PIN = const(5)  # data/command
DISPLAY_DO_PIN = const(6)  # data out toward screen/MOSI
DISPLAY_SCK_PIN = const(8)  # clock
DISPLAY_CS_PIN = const(9)  # chip select
DISPLAY_BL_PIN = const(10)  # backlight

DISPLAY_DMA = const(0)
DISPLAY_DMA_ABORT_ADDRESS = const(0x50000000 + 0x464)

SCREEN_HEIGHT = const(240)
SCREEN_WIDTH = const(320)

I2C_SDA = const(2)
I2C_SCL = const(3)

IRDA_TX_PIN = const(26)  # different from the pico sdk definition
IRDA_RX_PIN = const(27)


############################### PIO1 base    IRQ0_INTE(nable)
# IRDA_RX_SM_IRQ0_INTE_REG = 0x5030_0000 + 0x170
# IRDA_RX_NOT_EMPTY_MASK = 0x01  # conveniently the last bit


RIGHT_BUTTON = const(16)
DOWN_BUTTON = const(17)
UP_BUTTON = const(18)
LEFT_BUTTON = const(19)
B_BUTTON = const(20)
A_BUTTON = const(21)
START_BUTTON = const(22)
SELECT_BUTTON = const(23)
FN_BUTTON = const(24)


NEOPIXEL_PIN = const(4)
NEOPIXEL_NUM_LEDS = const(9)


SPEAKER_OUT = const(25)

# SD card
SPI_DO = const(12)  # MISO
SD_CS = const(13)
SPI_CK = const(14)
SPI_DI = const(15)  # MOSI


SAO_USER1 = const(28)
SAO_USER2 = const(29)


# PIO allocation
# DREQ values from 12.6.4.1 in rp2350 datasheet

DISPLAY_PIO = const(0)
DISPLAY_SM = const(0)
DISPLAY_REQ_SEL = const(0)  # PIO0 TX0

NEOPIXEL_PIO = const(0)
NEOPIXEL_SM = const(1)
NEOPIXEL_REQ_SEL = const(1)  # PIO 0 TX 1


# the irda PIO is just about full of instructions.
# Maybe I could reuse it because CIR and IRDA can't be used at the same time?
# ehhhh

CIR_PIO = const(0)
CIR_RX_SM = const(2)
# CIR_TX_PIO = const(0)
# CIR_TX_SM = const(3)


IRDA_PIO = const(1)
IRDA_RX_SM = const(0)
IRDA_TX_SM = const(1)
IRDA_TX_REQ_SEL = const(9)  # PIO1 TX1

# this is taking up 1 instruction so it can go here
NOP_PIO = const(1)
NOP_SM = const(2)
NOP_REQ_SEL = const(10)  # PIO 1 TX 2
