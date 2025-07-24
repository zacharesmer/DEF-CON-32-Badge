import asyncio
import gc
import os
from lib.menu import MenuProgram, MenuOption
import json
import re
import builtin_programs.calibrate as calibrate


class MainMenu(MenuProgram):
    def __init__(self, badge):
        super().__init__(badge)
        self.current_program = None
        self.current_program_handle = None
        self.options = self.load_programs()
        self.title = "Home"

    def load_programs(self):
        # built in programs go here, files go in the directory "builtin_programs"
        progs = [
            MenuOption("IR Remote", modname="builtin_programs.ir_remote"),
            MenuOption("Blinkenlights", modname="builtin_programs.blinkenlights"),
            MenuOption("Paint", modname="builtin_programs.paint"),
            MenuOption("Choose Theme", modname="builtin_programs.choose_theme"),
            MenuOption("Calibrate", modname="builtin_programs.calibrate"),
            MenuOption("Wav Player", modname="builtin_programs.wav_player"),
            MenuOption("PNG Viewer", modname="builtin_programs.png_viewer"),
        ]
        # and load any others listed in `external_programs.json`
        valid_identifier_exp = re.compile("^[A-Za-z_][A-Za-z0-9_.]*$")
        try:
            with open("programs.json", "r") as f:
                ext = json.load(f)
                print(ext)
                if ext.get("programs") is not None:
                    for p in ext["programs"]:
                        print(p)
                        display_name = p.get("name")
                        modname = p.get("modname")
                        if (
                            modname is not None
                            and display_name is not None
                            and valid_identifier_exp.match(modname) is not None
                        ):
                            # print(p)
                            progs.append(MenuOption(display_name, modname=modname))
                        else:
                            print(
                                f"Invalid module name '{p}', see https://docs.python.org/3/reference/lexical_analysis.html#identifiers"
                            )
        except (OSError, ValueError) as e:
            # if the file doesn't exist or is invalid, make a new one
            print(f"Error loading programs: {e}")
            print("creating new file")
            with open("programs.json", "w") as f:
                json.dump(
                    {"programs": []},
                    f,
                )
        return progs

    def clean_up_program(self):
        """Un-set any buttons and irqs, change back to root directory"""
        ## most button irqs get set by the menu anyway
        # self.badge.up_button.irq(None)
        # self.badge.down_button.irq(None)
        # self.badge.a_button.irq(None)
        # self.badge.left_button.irq(None)
        # self.badge.right_button.irq(None)
        self.badge.screen.stop_continuous_refresh()
        self.badge.b_button.irq(None)
        self.badge.fn_button.irq(None)
        self.setup_buttons()
        # TODO: make this start an animation defined in the preferences instead
        self.badge.neopixels.fill((0, 0, 0))
        os.chdir("/")
        print(f"Free: {gc.mem_free()}")
        gc.collect()
        print(f"Free: {gc.mem_free()}")
        self.badge.animation = None

    def select(self, *args):
        print(f"Selected {self.current_selection}")
        self.current_program_handle = asyncio.create_task(self.run_program())

    async def run_program(self):
        gc.collect()
        await self.close()
        ## danger danger
        # TODO: It would be good to store the programs in a folder.
        # maybe I can chdir into it? Other attempts did not work.
        # If you have an idea please send a PR because the root
        # directory is really cluttered with random garbage
        # and I wish it wasn't
        modname = self.options[self.current_selection].modname
        module = __import__(modname, None, None, ["Program"])
        self.current_program = module.Program(self.badge)
        print(f"Free: {gc.mem_free()}")
        gc.collect()
        print(f"Free: {gc.mem_free()}")
        await self.current_program.run()
        ## should get called in self.open()
        # self.clean_up_program()
        self.current_program = None
        del module
        asyncio.create_task(self.open())

    def menu_button_callback(self, *args):
        asyncio.create_task(self.open())

    async def open(self):
        # print(self.current_program)
        # stop the current program if it's running
        if self.current_program is not None:
            asyncio.create_task(self.current_program.exit())
            if self.current_program_handle is not None:
                await self.current_program_handle
                self.current_program_handle = None
        self.clean_up_program()
        self.setup_buttons()
        self.show()

    async def close(self):
        self.un_setup_buttons()
        self.badge.screen.frame_buf.fill(self.badge.theme.bg1)
        self.badge.screen.frame_buf.text("Loading...", 10, 10, self.badge.theme.fg1)
        self.badge.screen.draw_frame()

    # the main event loop
    async def run(self):
        prefs = self.badge.read_preferences()
        if prefs.get("x_calibration") is None or prefs.get("y_calibration") is None:
            await calibrate.Program(self.badge).run()
        await self.open()
        while True:
            if self.badge.animation is not None:
                self.badge.set_pixels(self.badge.animation.next())
            await asyncio.sleep(0)

    # no exit from the main menu
