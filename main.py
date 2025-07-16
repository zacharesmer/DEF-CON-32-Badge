"""
It lives!!!
"""

from machine import Pin
import board_config as bc
from badge import DC32_Badge
from main_menu import MainMenu
import asyncio


badge = DC32_Badge()
main_menu = MainMenu(badge)

badge.select_button.irq(main_menu.menu_button_callback, Pin.IRQ_FALLING)

asyncio.run(main_menu.run())
