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
        self.drawing_task = None
        self.hard_cancel_cb_ref = self.hard_cancel_cb

    def setup_image_buttons(self):
        super().un_setup_buttons()
        self.badge.b_button.irq(self.hard_cancel, Pin.IRQ_FALLING, hard=True)
        self.badge.a_button.irq(self.select, Pin.IRQ_FALLING)

    def hard_cancel(self, arg):
        self.stop_drawing = True
        micropython.schedule(self.hard_cancel_cb_ref, arg)

    def hard_cancel_cb(self, arg):
        self.mode = "File"
        # time.sleep_ms(30)
        self.badge.screen.rotate(0)
        super().setup_buttons()
        self.go_back(arg)

    def go_back(self, arg):
        if self.mode == "Showing":

            self.mode = "File"
            # self.stop_drawing
            # while self.currently_drawing:
            #     print(".", end="")
            #     asyncio.sleep(0)
            self.badge.screen.rotate(0)
        super().go_back(arg)

    def select(self, arg):
        # super goes first so that when a file is selected it falls through to here and immediately gets shown
        super().select(arg)
        if self.mode == "Showing":
            if not self.currently_drawing:
                self.badge.screen.rotate()
        elif self.mode == "File":
            self.mode = "Showing"
            self.png_task = asyncio.create_task(self.show_png())

    def decompress_and_draw(self, d):
        self.badge.screen.fill(self.badge.theme.bg1)
        self.badge.screen.draw_frame()
        last_line = array("B", [0 for _ in range(self.width * self.bytesPerPixel)])
        this_line = array("B", [0 for _ in range(self.width * self.bytesPerPixel)])
        raw_line = array("B", [0 for _ in range(self.width * self.bytesPerPixel)])
        pixel = [0, 0, 0, 0]
        for r in range(self.height):  # for each scanline
            # filter_type = int.from_bytes(d.read(1))  # first byte of scanline is filter type
            filter_type = d.read(1)  # first byte of scanline is filter type
            # print(filter_type)
            d.readinto(raw_line)
            for c in range(
                self.width * self.bytesPerPixel
            ):  # for each byte in scanline
                if self.stop_drawing:
                    return
                last_line[c] = this_line[c]
                # for i in range(bytesPerPixel):
                Filt_x = raw_line[c]
                if filter_type == b"\x00":  # None
                    Recon_x = Filt_x
                elif filter_type == b"\x01":  # Sub
                    Recon_x = Filt_x + (
                        this_line[c - self.bytesPerPixel]
                        if c >= self.bytesPerPixel
                        else 0
                    )
                elif filter_type == b"\x02":  # Up
                    Recon_x = Filt_x + (last_line[c] if r > 0 else 0)
                elif filter_type == b"\x03":  # Average
                    Recon_x = (
                        Filt_x
                        + (
                            (
                                this_line[c - self.bytesPerPixel]
                                if c >= self.bytesPerPixel
                                else 0
                            )
                            + (last_line[c] if r > 0 else 0)
                        )
                        // 2
                    )
                elif filter_type == b"\x04":  # Paeth
                    a = (
                        this_line[c - self.bytesPerPixel]
                        if c >= self.bytesPerPixel
                        else 0
                    )
                    b = last_line[c] if r > 0 else 0
                    c_pr = (
                        last_line[c - self.bytesPerPixel]
                        if r > 0 and c >= self.bytesPerPixel
                        else 0
                    )
                    p = a + b - c_pr
                    pa = abs(p - a)
                    pb = abs(p - b)
                    pc = abs(p - c_pr)
                    if pa <= pb and pa <= pc:
                        Pr = a
                    elif pb <= pc:
                        Pr = b
                    else:
                        Pr = c_pr
                    Recon_x = Filt_x + Pr
                else:
                    raise Exception("unknown filter type: " + str(filter_type))
                this_line[c] = Recon_x & 0xFF
                pixel[c % self.bytesPerPixel] = Recon_x & 0xFF
                if c % self.bytesPerPixel == 0 and not c == 0:
                    # if self.bytesPerPixel == 4:
                    #     color = rgba_to_565(*pixel[:])
                    # elif self.bytesPerPixel == 3:
                    # color = color565(*pixel[:3])
                    self.badge.screen.frame_buf.pixel(
                        c // self.bytesPerPixel + self.x_start,
                        r + self.y_start,
                        (
                            (pixel[0] & 0xF8) << 8
                            | (pixel[1] & 0xFC) << 3
                            | pixel[2] >> 3
                        ),
                    )
            if r % 2 == 0:
                self.badge.screen.draw_frame()

    # this is primarily from https://pyokagan.name/blog/2019-10-14-png/
    # Changes:
    #  - inlined calculations of adjacent pixels
    #  - use deflate.DeflateIO instead of zlib because that's the only option in micropython
    #  - but also it means we can stream the decoded pixels
    async def show_png(self):
        # self.setup_image_buttons()
        self.un_setup_buttons()
        self.badge.screen.fill(self.badge.theme.bg1)
        self.badge.screen.frame_buf.text("Loading...", 20, 20, self.badge.theme.fg1)
        self.badge.screen.draw_frame()
        self.stop_drawing = False
        gc.collect()
        self.currently_drawing = True
        try:
            # this is not ideal but there's not enough memory
            temp_file_name = f"{self.open_filename}.tmp"
            with open(self.open_filename, "rb") as f:
                if f.read(len(_PngSignature)) != _PngSignature:
                    raise Exception("Invalid PNG Signature")
                # what can I do so this is not all in memory at once?
                # chunks = []
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
                # center the image
                self.x_start = 0
                self.y_start = 0
                if self.width < bc.SCREEN_WIDTH:
                    self.x_start = (bc.SCREEN_WIDTH - self.width) // 2
                    # print(f"x_start : {x_start}")
                if self.height < bc.SCREEN_HEIGHT:
                    self.y_start = (bc.SCREEN_HEIGHT - self.height) // 2
                    # print(f"y_start : {y_start}")
                if compm != 0:
                    raise Exception("invalid compression method")
                if filterm != 0:
                    raise Exception("invalid filter method")
                if colort == 6:
                    self.bytesPerPixel = 4
                elif colort == 2:
                    self.bytesPerPixel = 3
                else:
                    raise Exception(
                        f"Invalid color space: {colort}. We only support truecolor with alpha"
                    )
                if bitd != 8:
                    raise Exception("we only support a bit depth of 8")
                if interlacem != 0:
                    raise Exception("we only support no interlacing")
                # i = 0
                self.setup_image_buttons()
                with open(temp_file_name, "rb") as tmp:
                    with DeflateIO(tmp, ZLIB) as d:
                        self.decompress_and_draw(d)
                self.badge.screen.draw_frame()
        except (Exception, MemoryError, OSError) as e:
            self.un_setup_buttons()
            print(e)
            eb = ErrorBox(self.badge, message=str(e.value))
            eb.display_error()
            self.mode = "Directory"
            self.setup_buttons()
            self.show()
        finally:
            self.setup_buttons()
            self.currently_drawing = False
            try:
                os.remove(temp_file_name)
            except:
                print(":/ couldn't remove temp file")

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


_PngSignature = b"\x89PNG\r\n\x1a\n"
