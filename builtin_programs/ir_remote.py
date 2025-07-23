# a program to be a TV remote! yay
import asyncio
import os

from lib.menu import MenuOption
from lib.file_browser import FileBrowserProgram
from lib.text_entry import TextEntry
from lib.common import timings_from_nec
from lib.yes_no_box import YesNoBox


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
                            line_in_file=line_in_file,
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
                                line_in_file=line_in_file,
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
            line_number += 1

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
            self.options.append(
                MenuOption(
                    "Rename Recording",
                    color=self.badge.theme.fg3,
                    ir_code=None,
                    action="Rename",
                )
            )

    # override
    async def make_new_file(self):
        self.un_setup_buttons()
        name = await TextEntry(self.badge, 16, "File name:").get_text()
        if name is not None:
            with open(f"{name}.{self.file_extension}", "w") as f:
                f.write("Filetype: IR signals file\nVersion: 1\n")
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
        self.un_setup_buttons()
        yes_no_box = YesNoBox(self.badge, "Delete recording?")
        answer = await yes_no_box.get_answer()
        if answer:
            print(f"Deleting recording {which_recording.name}")
            # print("Old file:\n")
            # with open(self.open_filename) as new_file:
            #     for l in new_file:
            #         print(l, end="")
            # print("\n**********\n")
            # move the file somewhere temporarily
            tmp_filename = f"{self.open_filename}.tmp"
            os.rename(self.open_filename, tmp_filename)
            # open the temp file
            with open(tmp_filename, "r") as tmp_file, open(
                self.open_filename, "w"
            ) as new_file:
                line_number = 0
                for line in tmp_file:
                    # if we've found the recording to delete, skip lines until the next recording starts (or EOF)
                    if line_number == which_recording.line_in_file:
                        line = tmp_file.readline()
                        line_number += 1
                        while not line.startswith("name") and not line == "":
                            line = tmp_file.readline()
                            line_number += 1
                        # this line is the first line from the next recording so we do want to copy it
                        new_file.write(line)
                    # otherwise just copy over the file
                    else:
                        new_file.write(line)
                        line_number += 1
            # clean up the temp file
            os.remove(tmp_filename)
            # print("New file:\n")
            # with open(self.open_filename) as new_file:
            #     for l in new_file:
            #         print(l, end="")
            # print("\n**********\n")
        self.setup_buttons()
        self.mode = "File"
        self.show(refresh=True)

    async def rename_recording(self, which_recording):
        # use a text input to get a new name
        # do the same as delete recording but just change the name
        self.un_setup_buttons()
        text_entry = TextEntry(self.badge, max_length=16, prompt="Recording name:")
        new_name = await text_entry.get_text()
        # it'll be None if the text entry was cancelled
        if new_name is not None:
            print(f"Renaming recording{which_recording.name} to {new_name}")
            # print("Old file:\n")
            # with open(self.open_filename) as new_file:
            #     for l in new_file:
            #         print(l, end="")
            # print("\n**********\n")
            # move the file somewhere temporarily
            tmp_filename = f"{self.open_filename}.tmp"
            os.rename(self.open_filename, tmp_filename)
            # open the temp file
            with open(tmp_filename, "r") as tmp_file, open(
                self.open_filename, "w"
            ) as new_file:
                line_number = 0
                for line in tmp_file:
                    # copy everything verbatim except the name of the renamed recording
                    if line_number == which_recording.line_in_file:
                        new_file.write(f"name: {new_name}\n")
                    else:
                        new_file.write(line)
                    line_number += 1
            # clean up the temp file
            os.remove(tmp_filename)
            # print("New file:\n")
            # with open(self.open_filename) as new_file:
            #     for l in new_file:
            #         print(l, end="")
            # print("\n**********\n")
        self.setup_buttons()
        self.mode = "File"
        self.show(refresh=True)
        pass
