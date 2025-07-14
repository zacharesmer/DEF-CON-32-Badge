"""
Adapted from the board definition in pico SDK: https://github.com/raspberrypi/pico-sdk/blob/master/src/boards/include/boards/defcon32_badge.h
"""

DISPLAY_DC_PIN = 5  # data/command
DISPLAY_DO_PIN = 6  # data out toward screen/MOSI
DISPLAY_SCK_PIN = 8  # clock
DISPLAY_CS_PIN = 9  # chip select
DISPLAY_BL_PIN = 10  # backlight

DISPLAY_DMA = 0
DISPLAY_DMA_ABORT_ADDRESS = 0x50000000 + 0x464

SCREEN_HEIGHT = 240
SCREEN_WIDTH = 320

I2C_SDA = 2
I2C_SCL = 3

IRDA_TX_PIN = 26  # different from the pico sdk definition
IRDA_RX_PIN = 27


############################### PIO1 base    IRQ0_INTE(nable)
# IRDA_RX_SM_IRQ0_INTE_REG = 0x5030_0000 + 0x170
# IRDA_RX_NOT_EMPTY_MASK = 0x01  # conveniently the last bit


RIGHT_BUTTON = 16
DOWN_BUTTON = 17
UP_BUTTON = 18
LEFT_BUTTON = 19
B_BUTTON = 20
A_BUTTON = 21
START_BUTTON = 22
SELECT_BUTTON = 23
FN_BUTTON = 24


NEOPIXEL_PIN = 4
NEOPIXEL_NUM_LEDS = 9


SPEAKER_OUT = 25

# SD card
SPI_DO = 12  # MISO
SD_CS = 13
SPI_CK = 14
SPI_DI = 15  # MOSI


SAO_USER1 = 28
SAO_USER2 = 29


# PIO allocation
# DREQ values from 12.6.4.1 in rp2350 datasheet

DISPLAY_PIO = 0
DISPLAY_SM = 0
DISPLAY_REQ_SEL = 0  # PIO0 TX0

NEOPIXEL_PIO = 0
NEOPIXEL_SM = 1
NEOPIXEL_REQ_SEL = 1  # PIO 0 TX 1


# the irda PIO is just about full of instructions.
# Maybe I could reuse it because CIR and IRDA can't be used at the same time?
# ehhhh

CIR_PIO = 0
CIR_RX_SM = 2
# CIR_TX_PIO = 0
# CIR_TX_SM = 3


IRDA_PIO = 1
IRDA_RX_SM = 0
IRDA_TX_SM = 1
IRDA_TX_REQ_SEL = 9  # PIO1 TX1

# this is taking up 1 instruction so it can go here
NOP_PIO = 1
NOP_SM = 2
NOP_REQ_SEL = 10  # PIO 1 TX 2
