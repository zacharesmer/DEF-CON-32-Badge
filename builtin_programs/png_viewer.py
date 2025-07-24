from lib.file_browser import FileBrowserProgram
import asyncio
import struct
import binascii
from deflate import DeflateIO, ZLIB
from array import array
from lib.common import color565
from io import BytesIO
import gc


class Program(FileBrowserProgram):
    def __init__(self, badge):
        super().__init__(
            badge, root_dir_name="images", file_extension="png", create_file=False
        )
        self.stop_drawing = False

    def just_the_back_button(self):
        super().un_setup_buttons()
        self.badge.b_button.irq(self.go_back)

    def go_back(self, arg):
        self.stop_drawing = True
        return super().go_back(arg)

    def select(self, arg):
        super().select(arg)
        if self.mode == "File":
            asyncio.create_task(self.show_png())

    # this is primarily from https://pyokagan.name/blog/2019-10-14-png/
    # Changes:
    #  - inlined calculations of adjacent pixels
    #  - use deflate.DeflateIO instead of zlib because that's the only option in micropython
    #  - but also it means we can stream the decoded pixels
    async def show_png(self):
        self.badge.screen.fill(self.badge.theme.bg1)
        self.stop_drawing = False
        gc.collect()
        with open(self.open_filename, "rb") as f:
            if f.read(len(_PngSignature)) != _PngSignature:
                raise Exception("Invalid PNG Signature")

            chunks = []
            while True:
                chunk_type, chunk_data = self.read_chunk(f)
                chunks.append((chunk_type, chunk_data))
                if chunk_type == b"IEND":
                    break

            _, IHDR_data = chunks[0]  # IHDR is always first chunk
            width, height, bitd, colort, compm, filterm, interlacem = struct.unpack(
                ">IIBBBBB", IHDR_data
            )
            if compm != 0:
                raise Exception("invalid compression method")
            if filterm != 0:
                raise Exception("invalid filter method")
            if colort != 6 and colort != 2:
                raise Exception(
                    f"Invalid color space: {colort}. We only support truecolor with alpha"
                )
            if bitd != 8:
                raise Exception("we only support a bit depth of 8")
            if interlacem != 0:
                raise Exception("we only support no interlacing")

            IDAT_data = b"".join(
                chunk_data for chunk_type, chunk_data in chunks if chunk_type == b"IDAT"
            )

            if colort == 6:
                bytesPerPixel = 4
            elif colort == 2:
                bytesPerPixel = 3
            # i = 0
            last_line = array("B", [0 for _ in range(width * bytesPerPixel)])
            this_line = array("B", [0 for _ in range(width * bytesPerPixel)])
            raw_line = array("B", [0 for _ in range(width * bytesPerPixel)])
            pixel = [0, 0, 0, 0]
            with DeflateIO(BytesIO(IDAT_data), ZLIB) as d:
                for r in range(height):  # for each scanline
                    # filter_type = int.from_bytes(d.read(1))  # first byte of scanline is filter type
                    filter_type = d.read(1)  # first byte of scanline is filter type
                    # print(filter_type)
                    d.readinto(raw_line)
                    for c in range(width * bytesPerPixel):  # for each byte in scanline
                        last_line[c] = this_line[c]
                        # for i in range(bytesPerPixel):
                        Filt_x = raw_line[c]
                        if filter_type == b"\x00":  # None
                            Recon_x = Filt_x
                        elif filter_type == b"\x01":  # Sub
                            Recon_x = Filt_x + (
                                this_line[c - bytesPerPixel]
                                if c >= bytesPerPixel
                                else 0
                            )
                        elif filter_type == b"\x02":  # Up
                            Recon_x = Filt_x + (last_line[c] if r > 0 else 0)
                        elif filter_type == b"\x03":  # Average
                            Recon_x = (
                                Filt_x
                                + (
                                    (
                                        this_line[c - bytesPerPixel]
                                        if c >= bytesPerPixel
                                        else 0
                                    )
                                    + (last_line[c] if r > 0 else 0)
                                )
                                // 2
                            )
                        elif filter_type == b"\x04":  # Paeth
                            a = (
                                this_line[c - bytesPerPixel]
                                if c >= bytesPerPixel
                                else 0
                            )
                            b = last_line[c] if r > 0 else 0
                            c_pr = (
                                last_line[c - bytesPerPixel]
                                if r > 0 and c >= bytesPerPixel
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
                        pixel[c % bytesPerPixel] = Recon_x & 0xFF
                        if c % bytesPerPixel == 0 and not c == 0:
                            self.badge.screen.frame_buf.pixel(
                                c // 4, r, color565(*pixel[:3])
                            )
                        if self.stop_drawing:
                            return
                    if r % 2 == 0:
                        self.badge.screen.draw_frame()
                    if self.stop_drawing:
                        return
            self.badge.screen.draw_frame()

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
_OS_TYPE_FILE = 0x8000
