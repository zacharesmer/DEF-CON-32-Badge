from lib import Color

builtin_themes = [
    {
        "name": "Engage",
        # main text color
        "fg1": [0x90, 0x90, 0x90],
        # secondary text color
        "fg2": [
            0xDB,
            0x16,
            0x75,
        ],
        # "foreground3": [0x89, 0x2B, 0xE1],
        "fg3": [0x0A, 0x79, 0x85],
        "fg4": [0x89, 0x2B, 0xE1],
        # something extra bright, for highlighting things
        "accent": [0xFF, 0xAC, 0x11],  # secondary text color
        # bg needs good contrast with fg colors
        "bg1": [
            0x11,
            0x11,
            0x11,
        ],
        "bg2": [0x34, 0x0D, 0x59],
    },
    {
        "name": "Access",
        "fg1": [0xBB, 0xBB, 0xBB],
        "fg2": [0x22, 0x88, 0x33],
        "fg3": [0xCC, 0xBB, 0x44],
        "fg4": [0x44, 0x77, 0xAA],
        "accent": [0xEE, 0x66, 0x77],
        "bg1": [
            0x11,
            0x11,
            0x11,
        ],
        "bg2": [0x5E, 0x1C, 0x42],
    },
]


class Theme:
    def __init__(self, theme_dict):
        self.name = theme_dict.get("name")
        self.fg1 = Color(*theme_dict.get("fg1"), "rgb")
        self.fg2 = Color(*theme_dict.get("fg2"), "rgb")
        self.fg3 = Color(*theme_dict.get("fg3"), "rgb")
        self.fg4 = Color(*theme_dict.get("fg4"), "rgb")
        self.accent = Color(*theme_dict.get("accent"), "rgb")
        self.bg1 = Color(*theme_dict.get("bg1"), "rgb")
        self.bg2 = Color(*theme_dict.get("bg2"), "rgb")


engage = Theme(builtin_themes[0])
access = Theme(builtin_themes[1])
