# Plan
- Use PIO to imlpement (some of, hopefully a lot of) IrDA SIR on the rasperry pi pico since the hardware available for it is dwindling
- Collect and archive information about IrDA SIR because the irda.org website is largely defunct

See [here](resources/Readme.md) for an index of some documents related to IrDA

# Managing Clock Drift

The modulation in the IrDA physical layer does not result in an IR pulse in every bit. This was an intentional part of the design and is meant to save power, but it presents a bit of a challenge when receiving a signal.

Once an IR pulse is seen, it starts the clock in the receiver. That clock runs independently and may start to drift from the clock in the transmitter. When I was testing with two rp2350s it took about 6000 32-bit words at 9600 baud to come out of sync, and only about 5 or so 32-bit words at 115200 baud. Clearly we need to manage it somehow.

The ideal way would be to restart the clock every time there is an IR pulse. Then, as long as there is a 0 transmitted reasonably often, it can run indefinitely. 

There are a few reasons that's not trivial. First, there's no notion of a timeout as part of the WAIT instruction in PIO, so I'd have to build one. I can't really busy wait in a loop because the amount of cycles per bit end up being too high to easily store in PIO registers. That is because of low power mode, which allows for the pulse to be as short as 1.6 us for any baud rate. Each bit at 9600 baud lasts 104 us, so the bit would need to be divided at least 64 times to detect the pulse at all, ideally more to detect it well. PIO registers can only store 5 bit numbers, so I'd need to get creative, and I'd like to avoid getting even further into the weeds for now if I can.

---

A less general possibility is not to present an interface directly to the EnDec at all. Instead I can provide a UART interface, where it stuffs data into/out of UART frames and translates it to/from IR all in one shot. This is how the PL011 UART works, and there are actually vestigial registers to control the IrDA output in the RP2350 datasheet. If I want to be cheeky I could use them... 

The MCP2140A chip sends UART frames over IR and claims it is standards compliant, so I'm going to take that as permission to do the same: https://ww1.microchip.com/downloads/en/DeviceDoc/22050a.pdf

The physical layer standard's example implementation also sends a UART frame, and mentions that each byte is asynchronous. That section is non-normative but if it *can* be done that way, I'm inclined to. I'm just not sure what other devices do/did, and the whole point of this is to be compatible with other things. But let's try it!

# Credit, citations, etc.
## Raspberry Pi RP2350 documentation and examples
- https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html
- https://github.com/raspberrypi/pico-sdk
- https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf

## Micropython documentation and examples
- https://docs.micropython.org/en/latest/library/rp2.html
- https://github.com/micropython/micropython/tree/master/examples/rp2

## Other
- DEFCON 32 badge firmware