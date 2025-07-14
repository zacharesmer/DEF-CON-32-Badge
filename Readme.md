# DEF CON 32 Badge Micropython Noun
A launcher and some programs that use most of the hardware--IrDA, neopixels, touch screen, etc.

All written in Micropython, so no need to compile extra C modules unless you really want to. To use the SD card you do need to set a couple of special flags when compiling MicroPython, but there are also pre-compiled UF2s.

If you have an extra PSRAM chip soldered on, there's also uf2 to actually take advantage of it (as much as micro python can, anyway). If you don't have that and you're interested, get yourself a APS6404L-3SQR-SN and stick it in the blank spot next to the D-Pad.

# Thank you
Thanks to Entropic Engineering for making a very cool and fun piece of hardware. Additional credit for various helpful things, examples, tutorials, and prior art:

- https://github.com/russhughes/st7789py_mpy
- https://github.com/russhughes/st7789_mpy
- https://github.com/peterhinch/micropython-nano-gui
- https://github.com/Phaeilo/dc32_badge_micropython
- https://github.com/p0ns/micropython-dc32
- https://dmitry.gr/?r=06.%20Thoughts&proj=09.ComplexPioMachines
- https://github.com/Wind-stormger/micropython-uasycio-buzzer
- Dmitry Grinberg's original badge firmware, which is in Discord somewhere

# Installing
If you have the extra PSRAM soldered on, you can use the "-with-PSRAM" uf2 files instead. 

## Option 1: Easiest
![a picture of the def con badge, ears at the bottom, screen facing away. The four buttons on the back are highlighted: top left - red, bottom left - green, top right - yellow, bottom right - blue](badgeback.png)

1. Hold the badge ears down with the screen facing away from you.
2. Plug the badge into your computer
3. Hold top right button (yellow)
4. Tap bottom right button (blue)
5. A drive called RP2350 should appear mounted on your computer
6. Drag `firmware-with-frozen-modules.uf2` into drive
7. Badge should reboot automatically with new firmware

## Option 2: For development
Use this option if you want to make changes to the firmware.

Perform the steps above, but use the file `firmware-empty.uf2`

Using mpremote, Thonny, VSCode with MicroPico, or plain old file explorer since it's got USB MSC enabled, copy everything listed in manifest.py over to the badge. Restart it and main.py should run. 

I also found it helpful to rename `main.py` when actively working on this so it wouldn't automatically start. That was resetting it gave me a chance not to run whatever bug I'd just written.

# Configuration
The system configuration (colors, animations, calibration, etc.) is written to a json file in the flash memory, so it should persist across restarts. If it's missing or has gotten messed up somehow, the badge will make a new, blank file. 

# IR Remote
You can use your badge as a TV remote! Currently it can only record and replay raw signals, so it won't work with existing recordings where the signal has been decoded, but I want to fix that soon. If you would like to help add support for a protocol, feel free! The easiest way to do it would be generating an array/list of timings, then sending it using the already made `send_timings` function. 

You can save and read files to/from the SD card, or to the flash memory if an SD card is not detected.

# Paint
Draw on the screen and send your drawing to another person through the retro-futuristic magic of Infrared! 

(note: this app uses IrDA SIR and is not compatible with the Flipper or other universal remotes that are expecting a carrier wave)

## Controls

Left: Wait to receive a drawing

Right: Send your drawing

B: Undo

A: Redo

Start: Clear screen

Select: Menu (to be implemented)

# Adding other programs

# WARNINGS
Any program you put on the badge can execute arbitrary MicroPython code with no guardrails whatsoever. If you have a DEF CON badge you probably have some idea of how dangerous that could be. Someone could make your badge **emulate a keyboard and mouse and generate arbitrary input to your computer over USB**, so please be careful. It's no more or less safe than downloading a different random uf2 and flashing your badge, but if I use the word "app" someone might get the idea there's any sandboxing whatsoever. You have been warned!

This uses the experimental SD card and USB MSC compile flags, which may lead to **data corruption**. Please keep a backup of anything you care about on your SD card or in the flash memory! It uses IR files compatible with the Flipper, but please don't put your Flipper SD card into this thing without a backup.

A lot of ink has been spilled in the [Micropython Github issues](https://github.com/micropython/micropython/issues/8426) about why USB MSC is problematic and should not be enabled. Both the computer and the micro controller may end up trying to write to the file system with different understandings of what is stored in it and where, and this kills the file system. 

Please don't store the only copy of anything important on the SD card you're putting into the badge!

## Adding a program
Place a python file into the flash memory, and add its module name to the list in `programs.json`. It will be put in the menu and when the badge starts up. 

The file should have a .py extension and be a valid Python module name: all lower case, can contain underscores, can contain numbers but does not start with a number. This is because it's just being loaded as a Python module. It may be easiest to copy the example in your_module_here.py and edit it.

# Plans for the future and ideas if you want to contribute
(A very non-exhaustive list, there is a lot that could be done!)

[] Use the accelerometer somehow (to change the screen rotation some work also needs to be done on stopping the display DMA loop without a hard reset. That would have the added benefit of letting apps opt in to manual screen redraws, which would help avoid tearing. Suggestions and PRs welcome!)
[] Use the RTC to keep track of the actual date and time
[] Whatever you can dream up for the SAO port
[] Neopixel animations!
[] Display images from a file on the screen (I think if you can convert them to bitmaps using RGB565 colors, it should be easy to dump them into the framebuf, I just haven't tried yet)
[] Decode more IR formats
[] Make it possible to delete and rename recordings/files/directories from the IR remote app
[] Something to use the speaker, maybe a piano app? 
[] Add a way to display text in other sizes and fonts (this is a solved problem in the russ hughes st7789 driver and micropython nano gui, but I haven't investigated how they did it yet. Nano gui is probably most similar because it uses framebufs)
[] literally any decently usable tools for layouts and UI