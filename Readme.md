# DEF CON 32 Badge Micropython Thing
Some example programs and a launcher that exercise most of the hardware--IrDA, neopixels, touch screen. It's all written in Micropython, so no need to compile extra C modules unless you really want to. To use the SD card you do need to set a couple of special flags when compiling MicroPython but it's not too scary, I promise.

I will make a version of this with the main python modules frozen in, and USB mass storage support, so you can plug it in and load images and things into the flash. I would love to get the SD card accessible but doing that in MicroPython has turned out to be complicated and mostly unexplored territory.

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
This will execute arbitrary MicroPython code with no guardrails whatsoever. If you have a DEF CON badge you probably have some idea of how dangerous that could be. Someone could make your badge **emulate a keyboard and mouse and generate arbitrary input to your computer**, so please be careful if you plan to plug this into your computer. It's no more or less safe than downloading a different random uf2 and flashing your badge, but if I accidentally use the word "app" someone might get the idea there's any sandboxing whatsoever. You have been warned!

Using the experimental SD card and USB MSC compile flags may cause **data corruption**. Please keep a backup of anything you care about on your SD card or in the flash memory! Yes it uses IR files compatible with the Flipper, but please don't put your Flipper SD card into this thing without a backup.

A lot of ink has been spilled in the Micropython Github issues about why USB MSC is Bad and should not be enbaled. Both the computer and the micro controller may end up trying to write to the same file system, and this kills the file system. To use this you need to promise not to store anything important on your badge and that you won't get mad when your data gets corrupted. Try to avoid editing things in flash from the computer, or at least restart the badge after doing it. 

## Adding a program
Place a python file into the flash memory, and register it in the list of apps in a JSON file somewhere (tbd). It will be put in the menu and when the badge starts up, some entry point will be called with the badge object as an argument (exact API TBD). When it exits, a teardown method will be called.

# Plans for the future and ideas if you want to contribute
(A very non-exhaustive list)

[] Use the accelerometer (to change the screen rotation some work also needs to be done on stopping the DMA loop without a hard reset. That would have the added benefit of letting apps opt in to manual screen redraws, which would help avoid tearing. I just haven't looked too hard into it yet.)
[] Use the RTC to keep track of the actual date and time
[] Whatever you can dream up for SAO interactions
[] More neopixel animations!
[] Display images on the screen (I think if you can convert them to bitmaps it should be easy to dump them into the framebuf, I just haven't tried)
[] Decode more IR formats
[] Make it possible to delete and rename recordings/files/directories from the IR remote app
[] Something to exercise the speaker, maybe a piano app? 