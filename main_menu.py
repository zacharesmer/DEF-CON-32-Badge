import board_config as bc
from machine import Timer, Pin
from screen.st7789v_definitions import WHITE, BLACK
import asyncio
import gc
import os
from menu import MenuProgram, MenuOption
import json
import re
import calibrate


class MainMenu(MenuProgram):
    def __init__(self, badge):
        self.badge = badge
        self.current_selection = 0
        self.current_program = None
        self.current_program_handle = None
        self.options = self.load_programs()
        self.title = "Home"
        super().__init__(badge)

    def load_programs(self):
        # built in programs go here
        progs = [
            MenuOption("ir_remote"),
            MenuOption("calibrate"),
            MenuOption("paint"),
            MenuOption("choose_theme"),
        ]
        # and load any others registered in `external_programs.json`
        valid_identifier_exp = re.compile("^[A-Za-z_][A-Za-z0-9_]*$")
        try:
            with open("programs.json", "r") as f:
                ext = json.load(f)
                if ext.get("programs") is not None:
                    for p in ext["programs"]:
                        if valid_identifier_exp.match(p) is not None:
                            print(p)
                            progs.append(MenuOption(p))
                        else:
                            print(
                                f"Invalid module name '{p}', see https://docs.python.org/3/reference/lexical_analysis.html#identifiers"
                            )
        except OSError as e:
            # if the file doesn't exist make a new one
            print(e)
            with open("programs.json", "w") as f:
                json.dump(
                    {
                        "programs": [
                            "your_module_here",
                        ]
                    },
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
        self.badge.b_button.irq(None)
        self.setup_buttons()
        # TODO: make this start the default animation instead
        self.badge.neopixels.fill((0, 0, 0))
        os.chdir("/")
        print(f"Free: {gc.mem_free()}")
        gc.collect()
        print(f"Free: {gc.mem_free()}")

    def select(self, *args):
        print(f"Selected {self.current_selection}")
        self.current_program_handle = asyncio.create_task(self.run_program())

    async def run_program(self):
        gc.collect()
        await self.close()
        ## danger danger
        # TODO: I couldn't figure out how to store the programs in a folder and
        # still launch them. If you can figure that out please send a PR
        # because the root directory is really cluttered with random garbage
        # and I wish it wasn't
        modname = self.options[self.current_selection].name
        module = __import__(modname)
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

    # the main event loop
    async def run(self):
        prefs = self.badge.read_preferences()
        if prefs.get("x_calibration") is None or prefs.get("y_calibration") is None:
            await calibrate.Program(self.badge).run()
        await self.open()
        while True:
            await asyncio.sleep(0)

    # no exit from the main menu
