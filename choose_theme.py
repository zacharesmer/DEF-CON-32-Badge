import json
from themes import builtin_themes


class Program:
    def __init__(self, badge):
        # badge holds the currently set theme, loaded from prefs at startup
        self.badge = badge
        self.themes = self.load_themes()

    def load_themes(self):
        # load some built in themes
        themes = builtin_themes
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
                            themes.append(theme)
        except OSError as e:
            with open("themes.json", "w") as f:
                json.dump({"themes": []}, f)
        return themes

    def set_theme(self, theme):
        # write the selected theme to prefs.json
        prefs = self.badge.read_preferences()
        prefs["theme"] = theme
        self.badge.write_preferences(prefs)

    async def run(self):
        # show all currently set colors
        # make some way to choose from pre-defined themes
        # make some way to edit the colors which automatically sets the theme to custom if one is changed
        # allow saving a theme to the themes file
        pass

    async def exit(self):
        pass
