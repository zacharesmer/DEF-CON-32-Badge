# a program to be a TV remote! yay
import asyncio
import os
from menu import MenuProgram


class Program(MenuProgram):
    def __init__(self, badge):
        super().__init__(badge)
        # load a list of ir files stored in the folder "ir_recordings", or make the directory if it doesn't exist
        try:
            os.chdir("ir_recordings")
        except OSError as e:
            os.mkdir("ir_recordings")
            os.chdir("ir_recordings")
        # TODO: add support for subdirectories
        self.mode = "Directory"  # modes can be "Directory", "File", and others tbd
        # self.title = "IR Remote"
        self.current_selection = 0
        pass

    async def run(self):
        self.is_running = True
        self.show_files_in_current_directory()
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
                    name = "Unsupported format"
                    output.append((name, ()))
            elif split_line[0] == "data:":
                # print(split_line[1:])
                output.append((name, [int(i) for i in split_line[1:]]))
        return output

    def make_empty_ir_file(self, filename):
        with open(f"{filename}", "w") as f:
            f.write("Filetype: IR signals file\nVersion: 1")

    def select(self, *args):
        if self.mode == "Directory":
            # 0x4000 is directory, 0x8000 is a file
            if self.options[self.current_selection][1] == 0x4000:
                os.chdir(self.options[self.current_selection][0])
                self.show_files_in_current_directory()
            elif self.options[self.current_selection][1] == 0x8000:
                self.display_recordings_from_file(
                    self.options[self.current_selection][0]
                )
            # TODO: add "new file" and "new directory" options
        elif self.mode == "File":
            self.send_selected_code()
            # TODO: add "record a code" option
        # return super().select(*args)

    def go_back(self, arg):
        if self.mode == "File":
            self.show_files_in_current_directory()
        elif self.mode == "Directory":
            if os.getcwd() != "/ir_recordings":
                os.chdir("..")
                self.show_files_in_current_directory()
        # return super().go_back(arg)

    def show_files_in_current_directory(self):
        self.title = os.getcwd()
        self.mode = "Directory"
        self.current_selection = 0
        # add the names to a list of options, keep track of which one is selected
        # set the mode so the OK button callback reads and displays the file
        self.options = []
        for f in os.ilistdir(os.getcwd()):
            # store the file's name and type
            self.options.append((f[0], f[1]))
        self.show()

    def display_recordings_from_file(self, filename):
        self.current_selection = 0
        self.mode = "File"
        self.title = filename
        with open(f"{filename}", "r") as f:
            self.options = self.read_ir_file(f)
            # print(self.options)
        self.show()

    def send_selected_code(self):
        self.badge.cir.send_timings(self.options[self.current_selection][1])
