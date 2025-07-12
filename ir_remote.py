# a program to be a TV remote! yay
import asyncio
import os
from menu import MenuProgram
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
        # self.title = "IR Remote"
        self.current_selection = 0
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
        data = None
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
                    output.append((name, ()))
            elif split_line[0] == "data:":
                # print(split_line[1:])
                output.append((name, [int(i) for i in split_line[1:]]))
        return output

    # def append_ir_code(self, )

    def select(self, arg):
        if self.mode == "Directory":
            selection_name, selection_type = self.options[self.current_selection]
            # 0x4000 is directory, 0x8000 is a file
            if selection_type == _OS_TYPE_DIR:
                self.mode = "Directory"
                os.chdir(selection_name)
                self.show(refresh=True)
            elif selection_type == _OS_TYPE_FILE:
                self.mode = "File"
                self.show(refresh=True)
            # TODO: handle "new file" and "new directory" options
            elif selection_type == _TYPE_NEW_DIR:
                asyncio.create_task(self.make_new_dir())
                # open a text entry once that's a thing that exists
                pass
            elif selection_type == _TYPE_NEW_FILE:
                asyncio.create_task(self.make_new_file())
                pass
        elif self.mode == "File":
            self.send_selected_code()
            # TODO: handle "record a code" option
        # return super().select(*args)

    def go_back(self, arg):
        if self.mode == "File":
            self.mode = "Directory"
        elif self.mode == "Directory":
            if os.getcwd() != self.root_dir:
                os.chdir("..")
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
            # store the file's name and type
            self.options.append((f[0], f[1]))
        self.options.append(("New File", _TYPE_NEW_FILE))
        self.options.append(("New Dir", _TYPE_NEW_DIR))

    def refresh_recordings_from_current_file(self):
        filename = self.options[self.current_selection][0]
        self.title = filename
        with open(f"{filename}", "r") as f:
            self.options = self.read_ir_file(f)
            # print(self.options)
        # TODO: add an "Add" option, maybe in a special color or something
        self.options.append(("New Recording", None))
        # TODO: override show to color types of files differently
        # self.show()

    async def make_new_dir(self):
        self.un_setup_buttons()
        name = await TextEntry(self.badge).get_text(10)
        os.mkdir(name)
        self.setup_buttons()
        self.show(refresh=True)
        print(name)

    async def make_new_file(self):
        self.un_setup_buttons()
        name = await TextEntry(self.badge).get_text(10)
        self.make_empty_ir_file(f"{name}.ir")
        self.setup_buttons()
        self.show(refresh=True)

    def make_empty_ir_file(self, filename):
        with open(f"{filename}", "w") as f:
            f.write("Filetype: IR signals file\nVersion: 1")
        print("made a file :)")

    def send_selected_code(self):
        self.badge.cir.send_timings(self.options[self.current_selection][1])


_OS_TYPE_FILE = 0x8000
_OS_TYPE_DIR = 0x4000
# these numbers are pretty arbitrary, could be changed if they cause a problem
_TYPE_NEW_FILE = 0x8001
_TYPE_NEW_DIR = 0x4001
_TYPE_DELETE_FILE = 0x8002
_TYPE_DELETE_DIR = 0x4002
