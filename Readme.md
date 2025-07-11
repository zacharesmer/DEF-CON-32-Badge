# DEF CON 32 Badge Micropython Toys
Some example programs and a launcher that use the IrDA module, neopixels, and touch screen of the DC32 badge. It's all written in Micropython, so no need to compile extra C modules unless you really want to. 

I will make a version of this with the main python modules frozen in, and USB mass storage support, so you can plug it in and load images and things into the flash. I would love to get the SD card accessible but doing that in MicroPython has turned out to be complicated and mostly unexplored territory, so I haven't.

If you have an extra PSRAM chip soldered on, there's also uf2 to actually take advantage of it (as much as micro python can, anyway). If you don't have that and you're interested, get yourself a APS6404L-3SQR-SN and stick it in the blank spot next to the D-Pad.

# Configuration
The system configuration (colors, animations, calibration, etc.) is written to a json file in the flash memory, so it should persist across restarts. If it's gotten messed up somehow, the badge will attempt to regenerate a blank file. There is also a default file in this repo you can copy over.

# IR Remote
Yes, you can use your badge as a TV remote! Currently it can only record and replay raw signals, so it won't work with most existing recordings, but I want to fix that soon. If you would like to help add support for a protocol, feel free! The easiest way to do it would be generating an array/list of timings, then sending it using the already made `send_timings` function. It would also be useful to set up tools to parse IR files from the IR DB.

You can save and read files to/from the internal flash and the SD card. 

# Paint
Draw on the screen and send your drawing to another person with Infrared! 

Note: this app uses IrDA SIR and is not compatible with the Flipper or other universal remotes, because it does not use a carrier wave. 

## Controls

Left: Wait to receive a drawing

Right: Send your drawing

B: Undo

A: Redo

Start: Clear screen

Select: Menu (to be implemented)

# Adding other programs

# WARNINGS
This will execute arbitrary Micro Python code with no guardrails whatsoever. If you have a DEF CON badge you probably have some idea of how dangerous that could be, but if you are not sufficiently alarmed, look up the USB Rubber Ducky. Someone could make your badge **emulate a keyboard and mouse and generate arbitrary input to your computer**, so please be careful if you plan to plug this into your computer. 

Someone could also **write arbitrary registers** on the chip, which could do nasty things to your badge. I don't know enough to determine whether you can actually enable secure boot or write OTP (one time programmable) registers from micro python, but if you can it would be possible to **permanently brick the badge**. Not just a cute little "put it in BOOTSEL mode and reflash it" brick, actually totally brick it unless you feel like [exploiting this hardware vulnerability](https://www.raspberrypi.com/news/security-through-transparency-rp2350-hacking-challenge-results-are-in/) or soldering on a new rp2350. You have been warned, please be careful!

Exposing the flash memory as a USB device can also cause **data corruption**. A lot of ink has been spilled in the Micropython Github issues about why this is Bad. Both the computer and the micro controller may end up trying to write to the same file system, and this kills the file system. If you pinky promise not to store anything important on your badge and you won't get mad when your data gets corrupted, you can use the UF2 with the file system exposed as a USB mass storage device. If you don't want to, you can also use mpremote or Thonny to upload files to the badge.

## Adding a program
Place a python file into the flash memory, and register it in the list of apps in a JSON file somewhere (tbd). It will be put in the menu and when the badge starts up, some entry point will be called with the badge object as an argument (exact API TBD). When it exits, a teardown method will be called.

