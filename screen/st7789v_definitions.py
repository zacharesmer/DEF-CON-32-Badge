# ST7789 commands
_ST7789_SWRESET = b"\x01"
_ST7789_SLPIN = b"\x10"
_ST7789_SLPOUT = b"\x11"
_ST7789_NORON = b"\x13"
_ST7789_INVOFF = b"\x20"
_ST7789_INVON = b"\x21"
_ST7789_DISPOFF = b"\x28"
_ST7789_DISPON = b"\x29"
_ST7789_CASET = b"\x2a"
_ST7789_RASET = b"\x2b"
_ST7789_RAMWR = b"\x2c"
_ST7789_VSCRDEF = b"\x33"
_ST7789_COLMOD = b"\x3a"
_ST7789_RAMWRC = b"\x3c"
_ST7789_MADCTL = b"\x36"
_ST7789_VSCSAD = b"\x37"
_ST7789_RAMCTL = b"\xb0"
_ST7789_PORCTRL = b"\xb2"
_ST7789_GATECTRL = b"\xb7"
_ST7789_GAMEN = b"\xba"
_ST7789_VCOMS = b"\xbb"
_ST7789_LCMCTRL = b"\xc0"
_ST7789_VDVVRHEN = b"\xc2"
_ST7789_VRHS = b"\xc3"
_ST7789_VDVS = b"\xc4"
_ST7789_PVGAMCTRL = b"\xe0"
_ST7789_NVGAMCTRL = b"\xe1"

# MADCTL bits
_ST7789_MADCTL_MY = const(0x80)
_ST7789_MADCTL_MX = const(0x40)
_ST7789_MADCTL_MV = const(0x20)
_ST7789_MADCTL_ML = const(0x10)
_ST7789_MADCTL_BGR = const(0x08)
_ST7789_MADCTL_MH = const(0x04)
_ST7789_MADCTL_RGB = const(0x00)


RGB = 0x00
BGR = 0x08

# # Color modes
# _COLOR_MODE_65K = const(0x50)
# _COLOR_MODE_262K = const(0x60)
# _COLOR_MODE_12BIT = const(0x03)
# _COLOR_MODE_16BIT = const(0x05)
# _COLOR_MODE_18BIT = const(0x06)
# _COLOR_MODE_16M = const(0x07)

# Color definitions
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

_ENCODE_PIXEL = const(">H")
_ENCODE_PIXEL_SWAPPED = const("<H")
_ENCODE_POS = const(">HH")
_ENCODE_POS_16 = const("<HH")

# init tuple format (b'command', b'data', delay_ms)
_ST7789_INIT_CMDS = (
    (_ST7789_SWRESET, b"\x00", 100),
    (_ST7789_SLPOUT, b"\x00", 50),  # Exit sleep mode
    (_ST7789_COLMOD, b"\x55", 10),
    #####
    # TODO: consider factoring the rotation/window size stuff out so it is configurable
    # Possible rotations: b"\x00", b"\x60", b"\xc0", b"\x"a0"
    # This is also where RGB or BGR are set (| the value with 0x08)
    (_ST7789_MADCTL, b"\x60", 0),
    # set window to be full size, 320 px wide, 240 px tall
    # x end = 319 = 0000_0001_0011_1111 = 0x013F
    (_ST7789_CASET, b"\x00\x00\x01\x3f", 0),
    # y end = 239 = 0000_0000_1110_1111 = 0x00EF
    (_ST7789_RASET, b"\x00\x00\x00\xef", 0),
    #####
    (_ST7789_INVOFF, b"\x00", 10),
    (_ST7789_NORON, b"\x00", 10),
    # Set gamma curve positive and negative polarity, does it do anything though?
    # (_ST7789_PVGAMCTRL, b"\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17", 0),
    # (_ST7789_NVGAMCTRL, b"\xd0\x00\x02\x07\x0a\x28\x31\x54\x47\x0e\x1c\x17\x1b\x1e", 0),
    (_ST7789_DISPON, b"\x00", 10),
)
