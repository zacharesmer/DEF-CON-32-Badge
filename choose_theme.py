import json
from lib.themes import builtin_themes, Theme
from menu import MenuProgram, MenuOption
from lib.common import Color
from lib.animations import FadeThroughColors
from color_selector import ColorSelector

# TODO: theme customization


class Program(MenuProgram):
    def __init__(self, badge):
        super().__init__(badge)
        self.num_columns = 1
        self.options = self.load_menu_options()
        for o in self.options:
            if self.badge.theme.name == o.name:
                break
            self.current_selection += 1
        self.title = "Themes"
        self.swatch_start_x = 279
        self.swatch_start_y = 8
        self.swatch_size = 32

    def load_menu_options(self):
        opts = [
            MenuOption(t.name, theme=t, action="Existing theme")
            for t in self.load_themes()
        ]
        # opts.append(
        #     MenuOption(
        #         "Custom Theme", color=self.badge.theme.fg3, action="Custom Theme"
        #     )
        # )
        return opts

    def load_themes(self):
        # load some built in themes
        themes = [t for _, t in builtin_themes.items()]
        # now try to get other custom themes if they exist
        try:
            with open("themes.json", "r") as f:
                ext = json.load(f)
                if ext.get("themes") is not None:
                    for theme in ext["themes"]:
                        if (
                            "name" in theme
                            and "foreground1" in theme
                            and "foreground2" in theme
                            and "foreground3" in theme
                            and "accent" in theme
                            and "background1" in theme
                            and "background2" in theme
                        ):
                            themes.append(Theme(theme))
        except (OSError, ValueError) as e:
            print(f"Error loading themes: {e}")
            print("Making new empty file")
            with open("themes.json", "w") as f:
                json.dump({"themes": []}, f)
        return themes

    def save_theme_selection(self, theme):
        # write the selected theme to prefs.json
        prefs = self.badge.read_preferences()
        # print(prefs)
        # print(theme)
        prefs["theme"] = theme.to_json()
        self.badge.write_preferences(prefs)

    def go_left(self, arg):
        # return super().go_left(arg)
        pass

    def go_right(self, arg):
        # return super().go_right(arg)
        pass

    def select(self, arg):
        selection = self.options[self.current_selection]
        self.badge.theme = selection.theme
        self.save_theme_selection(selection.theme)
        # reload the current menu options to update their colors
        self.options = self.load_menu_options()
        self.show()

    def show(self):
        super().show()
        t = self.options[self.current_selection].theme
        x = self.swatch_start_x
        y = self.swatch_start_y
        colors = (t.fg1, t.fg2, t.fg3, t.fg4, t.accent, t.bg1, t.bg2)
        for i in range(len(colors)):
            self.badge.screen.frame_buf.rect(
                x, y, self.swatch_size, self.swatch_size, colors[i], True
            )
            # self.badge.neopixels[i] = colors[i]
            self.badge.animation = FadeThroughColors(colors)
            y += self.swatch_size
