# Contributing
Contributions are welcome! Apps, animations, and additions to the main firmware. There's plenty of low-hanging fruit!

# Building
At some point down the road I'd like to get this into a Github action to make it less "trust me bro install this uf2", but this is how it is for now.

To build a frozen uf2 from source:

1. Clone/download this repository.

2. Download [MicroPython](https://github.com/micropython/micropython) and follow [their instructions](https://docs.micropython.org/en/latest/develop/gettingstarted.html) to install any dependencies and get things set up.

3. To enable USB MSC (this makes the badge show up as flash media when plugged into a computer), edit `/ports/rp2/mpconfigport.h`

```diff
-#define MICROPY_HW_USB_MSC (0)
+#define MICROPY_HW_USB_MSC (1)
```

4. From the root of the micropython directory, run:

```make
make -j -C ports/rp2 BOARD=RPI_PICO2 FROZEN_MANIFEST="/path/to/this/repo/manifest.py"
```

There is a [defcon32_badge board definition](https://github.com/raspberrypi/pico-sdk/blob/master/src/boards/include/boards/defcon32_badge.h) in the pico SDK. I changed `/ports/rp2/boards/RPI_PICO2/mpconfigboard.cmake` to point to that instead of the [pico 2 one](https://github.com/raspberrypi/pico-sdk/blob/master/src/boards/include/boards/pico2.h), and to be honest I'm not 100% sure if it makes a difference.

If you have PSRAM and want to use it, add this to whichever board definitions file you're using (somewhere before the final `endif`):

```C
#define MICROPY_HW_PSRAM_CS_PIN (0)
#define MICROPY_HW_ENABLE_PSRAM (1)
```

There may be a way to pass these changes in on the command line instead of editing the files, but I am not a CMake wizard, so I do not know it.

This will hopefully generate several files, including `firmware.uf2` that end up in `/ports/rp2/BUILD-RPI_PICO2`. 

When compileing without the frozen modules I had to clear out the `/ports/rp2/BUILD-RPI_PICO2` directory. You can also use `make clean`, it just deletes the build directory.


# Architecture
## Badge object
The badge class is a container for all of the different hardware bits and bobs. You can directly interact with them since it's python and they're not private, or you can use some higher level convenience methods provided by the badge class.

## Configuration
There are some global software preferences stored in `preferences.json`. These are read when the badge is initialized, and written whenever they are changed in the settings.

## Neopixel Animations
The most important part!

To set an animation, just set badge.animation to an `Animation` object. An `Animation` has a next() method that updates itself and returns a list of values for the neopixels. 

The main loop in the main menu/launcher/shell/whatever it is, repeatedly calls `next()` on the `Animation` stored in badge.animation. Then it loads that value into the badge's neopixels. By default the neopixels are auto-written with DMA, so writing to the new values will only block the CPU for as long as it takes to update the values in the array.

There is a `Color` class in `lib/common.py` for convenience when working with the same color on the screen and on the pixels. When something tries to use a `Color` as an int, it returns the screen's packed pixel data. When something tries to use it as an iterator, it returns its rgb value.

## Programs

Programs can be loaded from additional files in flash memory. Just add the filename (sans .py) to the list of programs, and it can be launched from the main menu. Programs are only loaded at startup, so you also need to restart the badge.

Programs should not add an interrupt handler for the "Select" button, because that is the way back to the main menu. This is not enforced by the software in any way though, so good luck. 

A program class should present the following API:

### Constructor
`__init__(self, badge) `

Set up the program, allocate memory, register interrupt handlers, etc.

### Run 
`async def run(self)`

Do the stuff with the things. This needs to have a loop, ideally with `await asyncio.sleep(0)` in it so it can yield to other async coroutines. 

After the loop, do any teardown or shutdown activities you need to do (unregister any interrupt handlers, cancel any timers, save data, etc.)

### Exit

`async def exit(self)`

Stop the main loop of the program so it can fall through and do whatever cleanup it needs to do. This is called by the menu to stop a program.

### Lifecycle
When a program is selected to run in the menu:
- Menu removes the irqs from its buttons
- The program is constructed
- Program's run() method is scheduled using asyncio, and then the menu awaits its return

When a program is closed by pressing the select button to go back to the menu:
- The program's exit() method is run
- The menu's await gets fulfilled, and it removes the reference to the program so it can be garbage collected (eventually)

## Async
The graphics can optionally run entirely off-CPU, because the screen and neopixels refresh using DMA and PIO. That is disabled in the menu programs because it leads to screen flickering and tearing. If you want absolute maximum framerate even when you're blocking the CPU, look at paint.py to see how to set up the DMA loop and refresh the screen continuously without CPU involvement.

Main loops in programs should depend on a semaphore or some kind of signal triggered by awaiting `exit`, and any loops that you don't want to fully block the CPU should include `await asyncio.sleep()`.