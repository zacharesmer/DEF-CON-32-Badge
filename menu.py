import board_config as bc
from machine import Timer, Pin
from screen.st7789v_definitions import WHITE, BLACK
import asyncio
import gc
import os


class MainMenu:
    def __init__(self, badge):
        self.badge = badge
        self.current_selection = 0
        self.current_program = None
        self.current_program_handle = None
        self.load_programs()

    def load_programs(self):
        # built in programs go here
        self.programs = ["calibrate", "paint", "ir_remote"]
        # TODO: load others from flash
        # for f in os.ilistdir("programs"):
        #     print(f)

    def setup_buttons(self):
        self.badge.up_button.irq(self.go_up, Pin.IRQ_FALLING)
        self.badge.down_button.irq(self.go_down, Pin.IRQ_FALLING)
        self.badge.a_button.irq(self.select, Pin.IRQ_FALLING)
        pass

    def un_setup_buttons(self):
        self.badge.up_button.irq(None)
        self.badge.down_button.irq(None)
        self.badge.a_button.irq(None)

    def go_up(self, *args):
        print("up")
        self.current_selection = (self.current_selection - 1) % len(self.programs)
        self.show()

    def go_down(self, *args):
        print("down")
        self.current_selection = (self.current_selection + 1) % len(self.programs)
        self.show()

    def select(self, *args):
        print(f"Selected {self.current_selection}")
        self.current_program_handle = asyncio.create_task(self.run_program())

    async def run_program(self):
        gc.collect()
        await self.close()
        ## danger danger
        modname = self.programs[self.current_selection]
        mod = __import__(modname)
        # print(dir(mod))
        self.current_program = mod.Program(self.badge)
        print(f"Free: {gc.mem_free()}")
        gc.collect()
        print(f"Free: {gc.mem_free()}")
        await self.current_program.run()
        self.current_program = None
        self.mod = None
        print(f"Free: {gc.mem_free()}")
        gc.collect()
        print(f"Free: {gc.mem_free()}")
        await self.open()

    def show(self):
        left_margin = 40
        self.badge.screen.frame_buf.fill(BLACK)
        self.badge.screen.frame_buf.text("Menu", left_margin, 10, WHITE)
        # print the options
        height = 30
        for i, prog in enumerate(self.programs):
            if i == self.current_selection:
                self.badge.screen.frame_buf.text(">", left_margin - 15, height, WHITE)
            self.badge.screen.frame_buf.text(prog, left_margin, height, WHITE)
            height += 15

    def menu_button_callback(self, *args):
        asyncio.create_task(self.open())

    async def open(self):
        print(self.current_program)
        # stop the current program if it's running
        if self.current_program is not None:
            asyncio.create_task(self.current_program.exit())
            if self.current_program_handle is not None:
                await self.current_program_handle
                self.current_program_handle = None
        print(f"Free: {gc.mem_free()}")
        gc.collect()
        print(f"Free: {gc.mem_free()}")
        self.setup_buttons()
        self.show()

    async def close(self):
        self.un_setup_buttons()

    # the main event loop
    async def run(self):
        await self.open()
        while True:
            await asyncio.sleep(0)

    # no exit
