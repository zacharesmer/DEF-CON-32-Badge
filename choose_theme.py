import json
from themes import builtin_themes, Theme
from menu import MenuProgram, MenuOption
from lib import Color
from color_selector import ColorSelector


class Program(MenuProgram):
    def __init__(self, badge):
        super().__init__(badge)
        self.num_columns = 1
        ## for saving the current theme when we go to color mode
        # self.current_theme = 0
        # self.themes = [
        #     MenuOption(t.name, theme=t, action="Existing theme")
        #     for t in self.load_themes()
        # ]
        # self.themes.append(
        #     MenuOption("New Theme", color=self.badge.theme.fg3, action="New Theme")
        # )
        # for i, t in enumerate(self.themes):
        #     if t.name == self.badge.theme.name:
        #         self.current_selection = i
        #         self.current_theme = i
        #         break
        self.options = self.load_menu_options()
        self.title = "Themes"
        # self.mode = "Themes"
        # self.color_display_names = (
        #     "Foreground 1",
        #     "Foreground 2",
        #     "Foreground 3",
        #     "Foreground 4",
        #     "Accent",
        #     "Background 1",
        #     "Background 2",
        # )

    def load_menu_options(self):
        opts = [
            MenuOption(t.name, theme=t, action="Existing theme")
            for t in self.load_themes()
        ]
        opts.append(
            MenuOption("New Theme", color=self.badge.theme.fg3, action="New Theme")
        )
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
        except OSError as e:
            print(e)
            with open("themes.json", "w") as f:
                json.dump({"themes": []}, f)
        return themes

    def save_theme_selection(self, theme):
        # write the selected theme to prefs.json
        prefs = self.badge.read_preferences()
        print(prefs)
        print(theme)
        prefs["theme"] = theme.to_json()
        self.badge.write_preferences(prefs)

    def go_left(self, arg):
        return super().go_left(arg)

    def go_right(self, arg):
        return super().go_right(arg)

    def select(self, arg):
        selection = self.options[self.current_selection]
        self.badge.theme = selection.theme
        self.save_theme_selection(selection.theme)
        # reload the current menu options to update their colors
        self.options = self.load_menu_options()
        self.show()
        # if self.mode == "Themes":
        #     # we're always actually making a new theme, the only difference is which colors are initially selected
        #     color_initial_values = []
        #     if selection.action == "Existing theme":
        #         color_initial_values = [
        #             selection.theme.fg1,
        #             selection.theme.fg2,
        #             selection.theme.fg3,
        #             selection.theme.fg4,
        #             selection.theme.accent,
        #             selection.theme.bg1,
        #             selection.theme.bg2,
        #         ]
        #     elif selection.action == "Blank theme":
        #         color_initial_values = [Color(255, 255, 255, "rgb")] * len(
        #             self.color_display_names
        #         )
        #     self.mode = "Colors"
        #     self.options = [
        #         MenuOption(col_name, theme_color=Color(*initial_value, "rgb"))
        #         for col_name, initial_value in zip(
        #             self.color_display_names, color_initial_values
        #         )
        #     ]

        # elif self.mode == "Colors":
        #     new_color = ColorSelector(selection.theme_color)
        #     if new_color is not None:
        #         pass  # the color was edited, we are now in a ~~custom theme~~

    # def switch_modes(self):
    #     if self.mode == "Themes":
    #         self.mode == "Colors"
    #         self.options = self.colors
    #         self.current_selection = 0
    #     elif self.mode == "Colors":
    #         self.mode = "Themes"
    #         self.options = self.themes

    def show(self):
        # if self.mode == "Themes":
        super().show()
        # if self.mode == "Colors":
        #     pass

    # async def run(self):
    #     # show the names and swatches of all colors in the current theme
    #     # make a way to cycle through pre-defined themes (maybe left and right when that is selected)
    #     # make a way to edit the colors which automatically sets the theme to a new custom object if one is changed
    #     # option to save theme to the themes file
    #     pass

    # async def exit(self):
    #     pass
