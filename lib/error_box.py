import board_config as bc
import asyncio
from machine import Pin


class ErrorBox:
    def __init__(self, badge, message="Error!"):
        self.badge = badge
        self.message = message
        self.ok_text = "Dismiss"
        self.selection_made = False

    def setup_buttons(self):
        self.badge.a_button.irq(self.select, Pin.IRQ_FALLING)
        self.badge.b_button.irq(self.select, Pin.IRQ_FALLING)

    def un_setup_buttons(self):
        self.badge.a_button.irq(None)
        self.badge.b_button.irq(None)

    def select(self, *args):
        self.selection_made = True

    async def display_error_async(self):
        # show a pop up with the question and the yes/no text
        # set callbacks for the a and b buttons
        self.show()
        self.setup_buttons()
        while self.selection_made == False:
            asyncio.sleep(0)
        self.un_setup_buttons()

    # currently we need the regular blocking version of this for displaying errors outside of async functions (like in constructors and early setup)
    def display_error(self):
        # show a pop up with the question and the yes/no text
        # set callbacks for the a and b buttons
        self.show()
        self.setup_buttons()
        while self.selection_made == False:
            pass
        self.un_setup_buttons()

    def show(self):
        self.badge.screen.frame_buf.rect(
            20,
            20,
            bc.SCREEN_WIDTH - 40,
            bc.SCREEN_HEIGHT - 40,
            self.badge.theme.accent,
            True,
        )
        self.badge.screen.text_in_box(
            self.message,
            30,
            30,
            self.badge.theme.fg2,
            self.badge.theme.bg2,
            box_width=bc.SCREEN_WIDTH - 60,
            box_height=bc.SCREEN_HEIGHT - 60,
            fill=True,
        )
        self.badge.screen.frame_buf.text(
            self.ok_text,
            bc.SCREEN_WIDTH // 2 - ((len(self.ok_text) * 8) // 2),
            bc.SCREEN_HEIGHT - 50,
            self.badge.theme.fg3,
        )
        self.badge.screen.frame_buf.text(
            ">",
            bc.SCREEN_WIDTH // 2 - ((len(self.ok_text) * 8) // 2) - 10,
            bc.SCREEN_HEIGHT - 50,
            self.badge.theme.accent,
        )
        self.badge.screen.draw_frame()
