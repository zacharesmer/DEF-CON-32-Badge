# a program to be a TV remote! yay
import asyncio
import os
from menu import MenuProgram, MenuOption
from text_entry import TextEntry


class Program(MenuProgram):
    def __init__(self, badge):
        super().__init__(badge)
        # maybe the SD card didn't work right
        try:
            os.chdir("sd")
        except OSError as e:
            print(e)
        # load a list of ir files stored in the folder "ir_recordings", or make the directory if it doesn't exist
        try:
            os.chdir("ir_recordings")
        except OSError as e:
            os.mkdir("ir_recordings")
            os.chdir("ir_recordings")
        self.root_dir = os.getcwd()
        # TODO: add support for subdirectories
        self.mode = "Directory"  # modes can be "Directory", "File", and others tbd
        self.title = ""  # will be filled in later from current directory
        self.current_selection = 0
        self.open_filename = ""
        pass

    async def run(self):
        self.show(refresh=True)
        await super().run()

    async def exit(self):
        self.is_running = False

    def read_ir_file(self, f):
        # parse the data into an array of names and lists of timings
        output = []
        name = None
        line = f.readline()
        while line != "":
            split_line = line.split()
            # print(split_line[0])
            line = f.readline()
            if split_line[0] == "name:":
                # print(split_line)
                name = split_line[1]
            elif split_line[0] == "type:":
                if split_line[1] == "parsed":
                    name = "Unimplemented"
                    output.append(
                        MenuOption(
                            name, color=self.badge.theme.fg1, ir_code=(), action=None
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
                    print(e)
        return output

    # def append_ir_code(self, )

    def select(self, arg):
        selection = self.options[self.current_selection]
        if self.mode == "Directory":
            # 0x4000 is directory, 0x8000 is a file
            if selection.filetype == _OS_TYPE_DIR:
                self.mode = "Directory"
                os.chdir(selection.name)
                self.show(refresh=True)
            elif selection.filetype == _OS_TYPE_FILE:
                self.open_filename = selection.name
                self.mode = "File"
                self.show(refresh=True)
            elif selection.filetype == _TYPE_NEW_DIR:
                asyncio.create_task(self.make_new_dir())
                # open a text entry once that's a thing that exists
                pass
            elif selection.filetype == _TYPE_NEW_FILE:
                asyncio.create_task(self.make_new_file())
                pass
        elif self.mode == "File":
            if selection.action == "Send":
                self.send_selected_code()
            elif selection.action == "Record":
                asyncio.create_task(self.record_new_code())
            elif selection.action == None:
                print("no action")
                pass
        # return super().select(*args)

    def go_back(self, arg):
        if self.mode == "File":
            self.mode = "Directory"
        elif self.mode == "Directory":
            if os.getcwd() != self.root_dir:
                os.chdir("..")
            else:
                self.is_running = False
        elif self.mode == "Recording":
            self.badge.cir.cancel = True
        self.show(refresh=True)

    # refresh controls whether the view will be reset and the first item will be selected. If refresh is false, the menu is just getting redrawn
    def show(self, refresh=False):
        if refresh:
            self.current_selection = 0
            self.view_start = 0
            if self.mode == "File":
                self.refresh_recordings_from_current_file()
            elif self.mode == "Directory":
                self.refresh_files_in_current_directory()
        super().show()

    def refresh_files_in_current_directory(self):
        self.title = os.getcwd()
        # add the names to a list of options, keep track of which one is selected
        # set the mode so the OK button callback reads and displays the file
        self.options = []
        for f in os.ilistdir(os.getcwd()):
            # we store the file's name and type
            fname, ftype, *_ = f
            # only add directories and .ir files, and ignore hidden files
            if fname.endswith(".ir") and not fname.startswith("."):
                self.options.append(
                    MenuOption(fname, color=self.badge.theme.fg1, filetype=ftype)
                )
            elif ftype == _OS_TYPE_DIR and not fname.startswith("."):
                self.options.append(
                    MenuOption(fname, color=self.badge.theme.fg2, filetype=ftype)
                )

        self.options.append(
            MenuOption("New File", color=self.badge.theme.fg3, filetype=_TYPE_NEW_FILE)
        )
        self.options.append(
            MenuOption("New Dir", color=self.badge.theme.fg3, filetype=_TYPE_NEW_DIR)
        )

    def refresh_recordings_from_current_file(self):
        self.title = self.open_filename
        with open(f"{self.open_filename}", "r") as f:
            self.options = self.read_ir_file(f)
            # print(self.options)
        # TODO: add an "Add" option, maybe in a special color or something
        self.options.append(
            MenuOption(
                "New Recording",
                color=self.badge.theme.fg3,
                ir_code=None,
                action="Record",
            )
        )
        # self.show()

    async def make_new_dir(self):
        self.un_setup_buttons()
        name = await TextEntry(self.badge, 16, "Directory name:").get_text()
        if name is not None:
            os.mkdir(name)
        self.setup_buttons()
        self.show(refresh=True)
        print(name)

    async def make_new_file(self):
        self.un_setup_buttons()
        name = await TextEntry(self.badge, 16, "Directory name:").get_text()
        if name is not None:
            self.make_empty_ir_file(f"{name}.ir")
        self.setup_buttons()
        self.show(refresh=True)

    def make_empty_ir_file(self, filename):
        with open(f"{filename}", "w") as f:
            f.write("Filetype: IR signals file\nVersion: 1")
        print("made a file :)")

    def send_selected_code(self):
        # todo: when I support more types of signal, I'll decode them here before sending
        self.badge.cir.send_timings(self.options[self.current_selection].ir_code)

    # capture a new code and save it to the currently open file
    async def record_new_code(self):
        self.badge.screen.fill(self.badge.theme.bg1)
        self.badge.screen.frame_buf.text(
            "Wating for a signal!", 10, 10, self.badge.theme.fg1
        )
        self.mode = "Recording"
        code = await self.badge.cir.receive_one_signal()
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


_OS_TYPE_FILE = 0x8000
_OS_TYPE_DIR = 0x4000
# these numbers are pretty arbitrary, could be changed if they cause a problem
_TYPE_NEW_FILE = 0x8001
_TYPE_NEW_DIR = 0x4001
_TYPE_DELETE_FILE = 0x8002
_TYPE_DELETE_DIR = 0x4002
