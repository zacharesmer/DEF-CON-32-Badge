import board_config as bc
import asyncio
from machine import Pin


class YesNoBox:
    def __init__(self, badge, question="Yes or No", yes="Yes", no="No"):
        self.badge = badge
        self.question = question
        self.yes_text = yes
        self.no_text = no
        self.choice = False
        self.selection_made = False

    def setup_buttons(self):
        self.badge.a_button.irq(self.select, Pin.IRQ_FALLING)
        self.badge.b_button.irq(self.cancel, Pin.IRQ_FALLING)
        self.badge.left_button.irq(self.toggle, Pin.IRQ_FALLING)
        self.badge.right_button.irq(self.toggle, Pin.IRQ_FALLING)

    def un_setup_buttons(self):
        self.badge.a_button.irq(None)
        self.badge.b_button.irq(None)
        self.badge.left_button.irq(None)
        self.badge.right_button.irq(None)

    def select(self, *args):
        self.selection_made = True

    def cancel(self, *args):
        self.choice = False
        self.selection_made = True

    def toggle(self, *args):
        self.choice = not self.choice
        self.show()

    async def get_answer(self):
        # show a pop up with the question and the yes/no text
        # set callbacks for the a and b buttons
        self.show()
        self.setup_buttons()
        while self.selection_made == False:
            await asyncio.sleep(0)
        self.un_setup_buttons()
        return self.choice

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
            self.question,
            30,
            30,
            self.badge.theme.fg2,
            self.badge.theme.bg2,
            box_width=bc.SCREEN_WIDTH - 60,
            box_height=bc.SCREEN_HEIGHT - 60,
            fill=True,
        )
        self.badge.screen.frame_buf.text(
            self.no_text,
            50,
            bc.SCREEN_HEIGHT - 50,
            self.badge.theme.fg3,
        )
        self.badge.screen.frame_buf.text(
            self.yes_text,
            bc.SCREEN_WIDTH - 50 - 8 * len(self.yes_text),
            bc.SCREEN_HEIGHT - 50,
            self.badge.theme.fg3,
        )

        if self.choice:
            cursor_x = bc.SCREEN_WIDTH - 50 - 8 * len(self.yes_text) - 10
        else:
            cursor_x = 40
        self.badge.screen.frame_buf.text(
            ">",
            cursor_x,
            bc.SCREEN_HEIGHT - 50,
            self.badge.theme.accent,
        )
        self.badge.screen.draw_frame()
