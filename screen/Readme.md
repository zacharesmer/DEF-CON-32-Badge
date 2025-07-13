# Fast micropython st7789 driver for pico

This is pretty much a wrapper for a micro python Framebuf that uses DMA to dump its contents onto an st7789 display. [According to this](https://docs.micropython.org/en/latest/library/rp2.DMA.html), DMA in Micro Python is only available on the Raspberry Pi Pico for now.

Framebufs have various built in methods to draw shapes and text:

https://docs.micropython.org/en/latest/library/framebuf.html

See `main.py` for some test patterns/example code

This does not have as many features as something like [micro python nano gui](https://github.com/peterhinch/micropython-nano-gui), or [russhughes' st7789_mpy](https://github.com/russhughes/st7789_mpy). Many thanks to them; their code was very helpful as an example of how to initialize and communicate with the display. Another helpful example was Dmitry Grinberg's def con 32 badge code, since that's the hardware I was working with.

There's also some code for the touch screen controller in the defcon 32 badge, but the calibration may be super wrong for everyone else's badge, no idea. And I would certainly not expect it to work with any other setup. Theoretically it looks like it should be able to use hardware I2C, but it said the pin was invalid when I tried, and I didn't spend much time chasing down why.

I used PIO to communicate with the screen because the badge has its screen attached to some pins that don't support hardware SPI. If you want to use this for some other project and you really need all the PIOs for something else, I believe SPI supports the buffer protocol so you could just change the DMA configuration to point to that (and change it to use the SPI DREQ signal).

# Ideas for improvements
This is pretty thrown together, so there are many:

- Shortly after making this I found LVGL and it seems to already have a driver that does something similar
- Explore double buffering
- The vsync related pins on the badge aren't hooked up, but if I did have them available I'd try to use them because there's a lot of tearing
- Find some way to get different fonts into a framebuf
- Find some way to display images (I think framebuf is basically a bitmap, so this may just be equivalent to converting it to a bitmap)
- Make it more configurable (different rotations, etc.).
- Hook up the neopixels
