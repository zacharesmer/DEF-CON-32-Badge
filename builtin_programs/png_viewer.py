from lib.file_browser import FileBrowserProgram
import asyncio
import struct
import binascii
from deflate import DeflateIO, ZLIB
from array import array
from lib.common import rgba_to_565, color565
from io import BytesIO
import gc
import board_config as bc
from lib.error_box import ErrorBox
import time
import os
from machine import Pin
import micropython


class Program(FileBrowserProgram):
    def __init__(self, badge):
        super().__init__(
            badge, root_dir_name="images", file_extension="png", create_file=False
        )
        self.stop_drawing = False
        self.currently_drawing = False
        self.image_open = False

    def setup_image_buttons(self):
        self.un_setup_buttons()
        self.badge.b_button.irq(self.hard_cancel, Pin.IRQ_FALLING, hard=True)
        self.badge.a_button.irq(self.select, Pin.IRQ_FALLING)

    def hard_cancel(self, arg):
        self.stop_drawing = True
        self.image_open = False

    def select(self, arg):
        # super goes first so that when a file is selected it falls through to here and immediately gets shown
        super().select(arg)
        if self.mode == "Showing":
            if not self.currently_drawing:
                self.badge.screen.rotate()
        elif self.mode == "File":
            self.mode = "Showing"
            self.un_setup_buttons()
            asyncio.create_task(self.show_png())

    @micropython.viper
    def decompress_and_draw(self: object, d: object):
        """
        reconstruct the stream of decompressed data into an image and draw it on the screen
        uses about 3 * image width in pixels * bytes per pixel bytes of memory
        """
        # this all looks totally wack but it's like 10x faster than when it looked readable
        # And errors in viper are... unforthcoming, so I don't want to change it much
        self.badge.screen.fill(self.badge.theme.bg1)
        self.badge.screen.draw_frame()
        height: int = int(self.height)
        width: int = int(self.width)
        bpp: int = int(self.bytesPerPixel)
        scale_x: int = int(int(self.scale) * bpp)
        scale_y: int = int(self.scale)
        x_start: int = int(self.x_start)
        y_start: int = int(self.y_start)
        draw_line: bool = False
        # hack to make 0 an object for the mpy-cross compiler
        last_line: ptr8 = ptr8(array("B", [abs(0) for _ in range(width * bpp)]))
        this_line: ptr8 = ptr8(array("B", [abs(0) for _ in range(width * bpp)]))
        raw_line_buf = array("B", [abs(0) for _ in range(width * bpp)])
        raw_line: ptr8 = ptr8(raw_line_buf)
        pixel: ptr8 = ptr8(array("B", [0, 0, 0, 0]))
        filter_type_buf = array("B", [0])
        filter_type: ptr8 = ptr8(filter_type_buf)
        a: int = int(0)
        b: int = int(0)
        c_pr: int = int(0)
        p: int = int(0)
        pa: int = int(0)
        pb: int = int(0)
        pc: int = int(0)
        Pr: int = int(0)
        r: int = int(0)
        c: int = int(0)
        for r in range(height):  # for each scanline
            if self.stop_drawing:
                return
            # filter type applies to the whole line
            d.readinto(filter_type_buf)  # first byte of scanline is filter type
            d.readinto(raw_line_buf)
            # only draw every scale_y'th line
            draw_line = r % scale_y == 0
            if filter_type[0] == 0:  # None
                for c in range(width * bpp):  # for each byte in scanline
                    if self.stop_drawing:
                        return
                    last_line[c] = this_line[c]
                    this_line[c] = raw_line[c]
                    pixel[c % bpp] = this_line[c] & 0xFF
                    if draw_line and c % scale_x == 0 and not c == 0:
                        self.badge.screen.frame_buf.pixel(
                            c // scale_x + x_start,
                            r // scale_y + y_start,
                            (
                                (pixel[0] & 0xF8) << 8
                                | (pixel[1] & 0xFC) << 3
                                | pixel[2] >> 3
                            ),
                        )
            elif filter_type[0] == 1:  # Sub
                for c in range(width * bpp):  # for each byte in scanline
                    if self.stop_drawing:
                        return
                    last_line[c] = this_line[c]
                    this_line[c] = (
                        raw_line[c] + (this_line[c - bpp] if c >= bpp else 0)
                    ) & 0xFF
                    pixel[c % bpp] = this_line[c] & 0xFF
                    if draw_line and c % scale_x == 0 and not c == 0:
                        self.badge.screen.frame_buf.pixel(
                            c // scale_x + x_start,
                            r // scale_y + y_start,
                            (
                                (pixel[0] & 0xF8) << 8
                                | (pixel[1] & 0xFC) << 3
                                | pixel[2] >> 3
                            ),
                        )
            elif filter_type[0] == 2:  # Up
                for c in range(width * bpp):  # for each byte in scanline
                    if self.stop_drawing:
                        return
                    last_line[c] = this_line[c]
                    this_line[c] = (raw_line[c] + (last_line[c] if r > 0 else 0)) & 0xFF
                    pixel[c % bpp] = this_line[c] & 0xFF
                    if draw_line and c % scale_x == 0 and not c == 0:
                        self.badge.screen.frame_buf.pixel(
                            c // scale_x + x_start,
                            r // scale_y + y_start,
                            (
                                (pixel[0] & 0xF8) << 8
                                | (pixel[1] & 0xFC) << 3
                                | pixel[2] >> 3
                            ),
                        )
            elif filter_type[0] == 3:  # Average
                for c in range(width * bpp):  # for each byte in scanline
                    if self.stop_drawing:
                        return
                    last_line[c] = this_line[c]
                    this_line[c] = (
                        raw_line[c]
                        + (
                            (this_line[c - bpp] if c >= bpp else 0)
                            + (last_line[c] if r > 0 else 0)
                        )
                        // 2
                    ) & 0xFF
                    pixel[c % bpp] = this_line[c] & 0xFF
                    if draw_line and c % scale_x == 0 and not c == 0:
                        self.badge.screen.frame_buf.pixel(
                            c // scale_x + x_start,
                            r // scale_y + y_start,
                            (
                                (pixel[0] & 0xF8) << 8
                                | (pixel[1] & 0xFC) << 3
                                | pixel[2] >> 3
                            ),
                        )
            elif filter_type[0] == 4:  # Paeth
                for c in range(width * bpp):  # for each byte in scanline
                    if self.stop_drawing:
                        return
                    last_line[c] = this_line[c]
                    a = this_line[c - bpp] if (c >= bpp) else 0
                    b = last_line[c] if r > 0 else 0
                    c_pr = last_line[c - bpp] if r > 0 and c >= bpp else 0
                    p = a + b - c_pr
                    pa = int(abs(p - a))
                    pb = int(abs(p - b))
                    pc = int(abs(p - c_pr))
                    if pa <= pb and pa <= pc:
                        Pr = a
                    elif pb <= pc:
                        Pr = b
                    else:
                        Pr = c_pr
                    this_line[c] = (raw_line[c] + Pr) & 0xFF
                    pixel[c % bpp] = this_line[c] & 0xFF
                    if draw_line and c % scale_x == 0 and not c == 0:
                        self.badge.screen.frame_buf.pixel(
                            c // scale_x + x_start,
                            r // scale_y + y_start,
                            (
                                (pixel[0] & 0xF8) << 8
                                | (pixel[1] & 0xFC) << 3
                                | pixel[2] >> 3
                            ),
                        )
            else:
                raise Exception("unknown filter type: " + str(filter_type[0]))
            if r % 4 == 0:
                self.badge.screen.draw_frame()
        # print("Done")

    # this is largely from https://pyokagan.name/blog/2019-10-14-png/
    # Changes:
    #  - inlined calculations of adjacent pixels
    #  - use deflate.DeflateIO instead of zlib because that's the only option in micropython
    #  - that's great for memory usage though, it means we can stream the decompressed data
    #  - add viper type annotations
    #  - turn it inside out and check the filter once for a slight speed boost at the cost of some repetition
    async def show_png(self):
        self.badge.screen.fill(self.badge.theme.bg1)
        self.badge.screen.frame_buf.text("Loading...", 20, 20, self.badge.theme.fg1)
        self.badge.screen.draw_frame()
        self.stop_drawing = False
        self.currently_drawing = True
        self.image_open = True
        gc.collect()
        try:
            # in which we basically use a file as swap space
            # why am I doing this?
            # the compressed data needs to be in a buffer so that DeflateIO can read it.
            # BytesIO has to fit in memory, and some images are too big, so that's a no go.
            # ideally I'd make my own stream class to take off the "IDAT" at the beginning
            # of each chunk and spit out the data, but that's not possible.
            # From the docs (https://docs.micropython.org/en/latest/library/io.html):
            # "Note that for efficiency, MicroPython doesn’t provide abstract base classes
            # corresponding to the hierarchy above, and it’s not possible to implement,
            # or subclass, a stream class in pure Python."
            temp_file_name = f"{self.open_filename}.tmp"
            with open(self.open_filename, "rb") as f:
                if f.read(len(_PngSignature)) != _PngSignature:
                    raise Exception("Invalid PNG Signature")
                with open(temp_file_name, "wb") as temp_file:
                    while True:
                        chunk_type, chunk_data = self.read_chunk(f)
                        if chunk_type == b"IDAT":
                            temp_file.write(chunk_data)
                        # chunks.append((chunk_type, chunk_data))
                        if chunk_type == b"IHDR":
                            IHDR_data = chunk_data
                        if chunk_type == b"IEND":
                            break
                # _, IHDR_data = chunks[0]  # IHDR is always first chunk
                self.width, self.height, bitd, colort, compm, filterm, interlacem = (
                    struct.unpack(">IIBBBBB", IHDR_data)
                )
                print(f"Width {self.width}, height {self.height}")
                # scale the image so it fits on the screen. Can only handle integer divisors, 1/1, 1/2, 1/3, etc.
                # Realistically past like 1/4th it'll probably be painfully slow to draw the image
                self.scale = 1
                while True:
                    if (
                        self.width // self.scale <= bc.SCREEN_WIDTH
                        and self.height // self.scale <= bc.SCREEN_HEIGHT
                    ):
                        break
                    self.scale += 1
                # center the image
                self.x_start = 0
                self.y_start = 0
                if self.width // self.scale < bc.SCREEN_WIDTH:
                    self.x_start = (bc.SCREEN_WIDTH - self.width // self.scale) // 2
                if self.height // self.scale < bc.SCREEN_HEIGHT:
                    self.y_start = (bc.SCREEN_HEIGHT - self.height // self.scale) // 2
                if compm != 0:
                    raise Exception(f"Invalid compression method: {compm}")
                if filterm != 0:
                    raise Exception(f"Invalid filter method: {filterm}")
                if colort == 6:
                    self.bytesPerPixel = 4
                elif colort == 2:
                    self.bytesPerPixel = 3
                else:
                    raise Exception(f"Invalid color space: {colort}")
                if bitd != 8:
                    raise Exception(
                        f"Invalid bit depth: {bitd}. Only supports a bit depth of 8"
                    )
                if interlacem != 0:
                    raise Exception(f"Does not support interlacing")
                self.setup_image_buttons()
                with open(temp_file_name, "rb") as tmp:
                    with DeflateIO(tmp, ZLIB) as d:
                        start = time.ticks_ms()
                        self.decompress_and_draw(d)
                        print(
                            f"displayed image in {time.ticks_diff(time.ticks_ms(), start)}ms"
                        )
                self.badge.screen.draw_frame()
        # show a nice error on the badge
        except (Exception, MemoryError, OSError) as e:
            # raise e
            self.un_setup_buttons()
            print(e)
            eb = ErrorBox(self.badge, message=str(e.value))
            eb.display_error()
            self.image_open = False
            self.mode = "Directory"
            self.setup_buttons()
            self.show()
        finally:
            self.currently_drawing = False
            self.stop_drawing = False
            try:
                os.remove(temp_file_name)
            except:
                print(":/ couldn't remove temp file")
        while self.image_open:
            await asyncio.sleep(0)
        self.setup_buttons()
        self.badge.screen.rotate(0)
        self.mode = "Directory"
        self.show()

    def read_chunk(self, f):
        # Returns (chunk_type, chunk_data)
        chunk_length, chunk_type = struct.unpack(">I4s", f.read(8))
        chunk_data = f.read(chunk_length)
        (chunk_expected_crc,) = struct.unpack(">I", f.read(4))
        chunk_actual_crc = binascii.crc32(
            chunk_data, binascii.crc32(struct.pack(">4s", chunk_type))
        )
        if chunk_expected_crc != chunk_actual_crc:
            raise Exception("chunk checksum failed")
        return chunk_type, chunk_data

    async def exit(self):
        print("??")
        self.stop_drawing = True
        self.image_open = False
        await super().exit()


_PngSignature = b"\x89PNG\r\n\x1a\n"
