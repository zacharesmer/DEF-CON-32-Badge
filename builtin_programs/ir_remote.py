# a program to be a TV remote! yay
import asyncio
import os

from lib.menu import MenuOption
from lib.file_browser import FileBrowserProgram
from lib.text_entry import TextEntry
from lib.common import timings_from_nec


class Program(FileBrowserProgram):
    def __init__(self, badge):
        super().__init__(
            badge,
            root_dir_name="ir_recordings",
            file_extension="ir",
        )

    async def run(self):
        self.badge.setup_ir("cir")
        await super().run()
        self.badge.cir = None

    async def exit(self):
        self.is_running = False

    def read_ir_file(self, f):
        # parse the data into an array of names and lists of timings
        # also store the line in the file where the recording starts for use when renaming and deleting
        output = []
        name = None
        line_in_file = None
        decode_nec = False
        decode_necext = False
        # TODO: other formats go here
        # decode_other_format = False
        address = None
        command = None
        line_number = 0
        for line in f:
            split_line = line.split()
            line_number += 1
            if split_line[0] == "name:":
                # print(split_line)
                name = split_line[1]
                line_in_file = line_number
            elif split_line[0] == "protocol:":
                if split_line[1] == "NEC":
                    decode_nec = True
                elif split_line[1] == "NECext":
                    decode_necext = True
                # TODO: more formats go here
                # elif split_lin[1] == "OtherFormat:"
                #   decode_other_format = True
                else:
                    name = "Unimplemented"
                    output.append(
                        MenuOption(
                            name,
                            color=self.badge.theme.fg1,
                            ir_code=(),
                            action=None,
                            line_in_file=line_in_file,
                        )
                    )
            elif split_line[0] == "data:":
                # print(split_line[1:])
                try:
                    output.append(
                        MenuOption(
                            name,
                            color=self.badge.theme.fg1,
                            ir_code=[int(i) for i in split_line[1:]],
                            action="Send",
                        )
                    )
                except Exception as e:
                    print(f"Error decoding raw IR signal: {e}")
            elif split_line[0] == "address:":
                if decode_nec:
                    # address = [int(i, 16) for i in split_line[1:]]
                    try:
                        address = int(split_line[1], 16)
                    except Exception as e:
                        print(f"Error decoding NEC address: {e}")
                elif decode_necext:
                    try:
                        address = int("".join(split_line[1:3]), 16)
                    except Exception as e:
                        print(f"Error decoding NEC address: {e}")
                # TODO: more formats go here
                # elif decode_other_format:
                #   get the address
            elif split_line[0] == "command:":
                if decode_nec or decode_necext:
                    # command = [int(i, 16) for i in split_line[1:]]
                    try:
                        if decode_nec:
                            command = int(split_line[1], 16)
                        elif decode_necext:
                            command = int("".join(split_line[1:3]), 16)
                        t = timings_from_nec(address, command, ext=decode_necext)
                        # print(f"got timings from NEC: {t}")
                        output.append(
                            MenuOption(
                                name,
                                color=self.badge.theme.fg1,
                                ir_code=t,
                                action="Send",
                            )
                        )
                    except Exception as e:
                        print(f"Error decoding NEC command or signal: {e}")
                    finally:
                        decode_nec = False
                        decode_necext = False
                # TODO: more formats go here
                # elif decode_other_format:
                #   make a menu option using the decoded timings

        return output

    def select(self, arg):
        selection = self.options[self.current_selection]
        if self.mode == "File":
            if selection.action == "Send":
                self.send_selected_code()
            elif selection.action == "Record":
                asyncio.create_task(self.record_new_code())
            elif selection.action == "Delete":
                self.mode = "Delete Recording"
                self.show(refresh=True)
            elif selection.action == "Rename":
                self.mode = "Rename Recording"
                self.show(refresh=True)
            elif selection.action == None:
                print("no action")
        elif self.mode == "Delete Recording":
            print(selection.action)
            # only delete valid recordings
            if selection.action == "Send":
                asyncio.create_task(self.delete_recording(selection))
        elif self.mode == "Rename Recording":
            # only rename valid recordings
            if selection.action == "Send":
                asyncio.create_task(self.rename_recording(selection))
        else:
            super().select(arg)

    def show(self, refresh=False):
        if refresh:
            if (
                self.mode == "File"
                or self.mode == "Delete Recording"
                or self.mode == "Rename Recording"
            ):
                self.refresh_file_contents()
        else:
            # if we're recording, return early so we don't draw any of the menu stuff
            # just refresh the screen from the framebuf
            if self.mode == "Recording":
                self.badge.screen.draw_frame()
                return
        super().show(refresh=refresh)

    def go_back(self, arg):
        print(f"Going back, current mode is {self.mode}")
        if self.mode == "Delete Recording" or self.mode == "Rename Recording":
            self.mode = "File"
        elif self.mode == "Recording":
            self.badge.cir.cancel = True
        else:
            return super().go_back(arg)
        self.show(refresh=True)

    def refresh_file_contents(self):
        if self.mode == "File":
            self.title = self.open_filename
            self.title_color = self.default_title_color
        elif self.mode == "Rename Recording":
            self.title = "Select a recording to rename"
            self.title_color = self.badge.theme.accent
        elif self.mode == "Delete Recording":
            self.title = "Select a recording to delete"
            self.title_color = self.badge.theme.accent

        with open(f"{self.open_filename}", "r") as f:
            self.options = self.read_ir_file(f)
            # print(self.options)
        if self.mode != "Rename Recording" and self.mode != "Delete Recording":
            self.options.append(
                MenuOption(
                    "New Recording",
                    color=self.badge.theme.fg3,
                    ir_code=None,
                    action="Record",
                )
            )
            self.options.append(
                MenuOption(
                    "Delete Recording",
                    color=self.badge.theme.fg3,
                    ir_code=None,
                    action="Delete",
                )
            )

    # override
    async def make_new_file(self):
        self.un_setup_buttons()
        name = await TextEntry(self.badge, 16, "File name:").get_text()
        if name is not None:
            with open(f"{name}.{self.file_extension}", "w") as f:
                f.write("Filetype: IR signals file\nVersion: 1")
            print("made a file :)")
        self.setup_buttons()
        self.show(refresh=True)

    def send_selected_code(self):
        # the codes are converted to timings when they're loaded from the file
        self.badge.cir.send_timings(self.options[self.current_selection].ir_code)

    # capture a new code and save it to the currently open file
    async def record_new_code(self):
        self.badge.screen.fill(self.badge.theme.bg1)
        self.badge.screen.frame_buf.text(
            "Waiting for a signal!", 10, 10, self.badge.theme.fg1
        )
        self.mode = "Recording"
        self.show()
        code = await self.badge.cir.receive_one_signal()
        print(f"recorded {code}")
        self.mode = "File"
        if code is not None:
            self.un_setup_buttons()
            name = await TextEntry(
                self.badge, 16, f"Got {len(code)} samples. Enter a name:"
            ).get_text()
            if name is not None:
                to_write = [
                    "#",
                    f"name: {name}",
                    "type: raw",
                    "frequency: 38000",
                    "duty_cycle: 0.330000",
                    f"data: {" ".join([str(t) for t in code])}",
                ]
                with open(self.open_filename, "a") as f:
                    f.write("\n".join(to_write))
                    f.write("\n")
            self.setup_buttons()
        self.show(refresh=True)

    async def delete_recording(self, which_recording):
        print(f"Deleting recording {which_recording.name}")
        # move the file somewhere temporarily
        # open the temp file
        # write each line from the temp file to the original file's location until we get to the recording to skip
        # skip lines until the start of the next recording (line starts with "name:")
        # write the rest of the file
        # delete the temp file
        self.mode = "File"
        self.show(refresh=True)
        pass

    async def rename_recording(self, which_recording):
        # use a text input to get a new name
        # do the same as delete recording but just change the name
        print(f"Renaming recording{which_recording} ({self.current_selection.name})")
        self.mode = "File"
        self.show(refresh=True)
        pass
