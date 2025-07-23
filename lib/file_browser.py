# a class that can be extended to make a file browser program
import asyncio
import os
from lib.menu import MenuProgram, MenuOption
from lib.text_entry import TextEntry
from lib.common import timings_from_nec
from lib.yes_no_box import YesNoBox
from lib.error_box import ErrorBox


class FileBrowserProgram(MenuProgram):
    def __init__(
        self,
        badge,
        root_dir_name="",
        file_extension="",
        create_dir=True,
        create_file=True,
        delete_file=True,
        delete_dir=True,
        rename_dir=True,
        rename_file=True,
    ):
        super().__init__(badge)
        # which directory will this program use to store its data
        self.root_dir_name = root_dir_name
        # what type of file can it interact with
        # later I can imagine wanting to make this use more than one extension...
        self.file_extension = file_extension
        # these determine which options for deleting/creating files to show
        # for example, in an audio player, you can't create files because there's no mic on the badge
        # opening files is always allowed because otherwise what is the point
        self.create_dir_option = create_dir
        self.create_file_option = create_file
        self.delete_dir_option = delete_dir
        self.delete_file_option = delete_file
        self.rename_dir_option = rename_dir
        self.rename_file_option = rename_file
        # maybe the SD card didn't work right, if it's not mounted just use flash
        try:
            os.chdir("sd")
        except OSError as e:
            print(f"SD card not available: {e}")
        # open this program's directory, or make it if it doesn't exist
        try:
            os.chdir(root_dir_name)
        except OSError as e:
            os.mkdir(root_dir_name)
            os.chdir(root_dir_name)
        # store the full path to the root directory (likely /sd/{root_dir_name})
        self.root_dir = os.getcwd()
        # TODO: add support for subdirectories
        self.mode = "Directory"  # modes can be "Directory", "File", and others tbd
        self.title = ""  # will be filled in later from current directory
        self.current_selection = 0
        self.open_filename = ""
        # set in menuprogram
        # self.title_color = self.badge.theme.fg3
        self.default_title_color = self.title_color
        self.dir_color = self.badge.theme.fg2
        self.file_color = self.badge.theme.fg1
        self.new_file_color = self.badge.theme.fg3
        self.new_dir_color = self.badge.theme.fg3
        self.rename_color = self.badge.theme.fg3
        self.delete_color = self.badge.theme.fg3
        self.cursor_color = self.badge.theme.accent

    async def run(self):
        self.show(refresh=True)
        # main loop runs in MenuProgram
        await super().run()

    async def exit(self):
        self.is_running = False

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
            elif selection.filetype == _TYPE_NEW_FILE:
                asyncio.create_task(self.make_new_file())
            elif selection.filetype == _TYPE_DELETE:
                # enter DeleteFile mode so you can select a directory and delete it
                self.mode = "Delete"
                self.show(refresh=True)
            elif selection.filetype == _TYPE_RENAME:
                # enter DeleteFile mode so you can select a directory and delete it
                self.mode = "Rename"
                self.show(refresh=True)

        elif self.mode == "Delete":
            if (
                selection.filetype == _OS_TYPE_DIR
                or selection.filetype == _OS_TYPE_FILE
            ):
                asyncio.create_task(self.delete(selection))

        elif self.mode == "Rename":
            if (
                selection.filetype == _OS_TYPE_DIR
                or selection.filetype == _OS_TYPE_FILE
            ):
                asyncio.create_task(self.rename(selection))

        elif self.mode == "File":
            print(
                "Implement the in-file selection actions in your child class then call super().select(arg)"
            )

    def go_back(self, arg):
        # print(f"Going back, current mode is {self.mode}")
        if self.mode == "File":
            self.mode = "Directory"
        elif self.mode == "Directory":
            if os.getcwd() != self.root_dir:
                os.chdir("..")
            else:
                self.is_running = False
        elif self.mode == "Rename":
            self.mode = "Directory"
        elif self.mode == "Delete":
            self.mode = "Directory"
        self.show(refresh=True)

    # `refresh` controls whether the view will be reset and the selection reset to the 1st item.
    # If refresh is false, we don't re-fetch the contents of the file or directory or reset the selection.
    # The menu just gets redrawn with the current options list and current selection.
    # refresh=False is  used when navigating the menu and changing the selected item, but nothing else
    def show(self, refresh=False):
        if refresh:
            self.current_selection = 0
            self.view_start = 0
            # handle refreshing the file contents in the child class
            # if self.mode == "File":
            #     self.refresh_file_contents()
            if (
                self.mode == "Directory"
                or self.mode == "Delete"
                or self.mode == "Rename"
            ):
                self.refresh_directory_contents()
        super().show()

    def refresh_directory_contents(self):
        # print("refreshing directory...")
        if self.mode == "Directory":
            self.title = os.getcwd()
            self.title_color = self.default_title_color
        elif self.mode == "Delete":
            self.title = "Select something to delete"
            self.title_color = self.badge.theme.accent
        elif self.mode == "Rename":
            self.title = "Select something to rename"
            self.title_color = self.badge.theme.accent
        # add the names to a list of options, keep track of which one is selected
        # set the type so the OK button callback knows if we selected a file or directory or special option
        self.options = []
        # if os.getcwd() != self.root_dir:
        #     self.options.append(
        #         MenuOption("..", color=self.badge.theme.fg2, filetype=_OS_TYPE_DIR)
        #     )
        #     self.current_selection = 1
        for f in os.ilistdir(os.getcwd()):
            # we store the file's name and type (type as in file or directory)
            fname, ftype, *_ = f
            # only add directories and files with the right extension, and ignore hidden files
            if (
                ftype == _OS_TYPE_FILE
                and fname.endswith(self.file_extension)
                and not fname.startswith(".")
            ):
                # if renaming or deleting is disabled for files or dirs, don't show the files and directories in delete/rename mode
                if self.mode == "Delete" and not self.delete_file_option:
                    continue
                elif self.mode == "Rename" and not self.rename_file_option:
                    continue
                else:
                    self.options.append(
                        MenuOption(fname, color=self.file_color, filetype=ftype)
                    )
            elif ftype == _OS_TYPE_DIR and not fname.startswith("."):
                if self.mode == "Delete" and not self.delete_dir_option:
                    continue
                elif self.mode == "Rename" and not self.rename_dir_option:
                    continue
                else:
                    self.options.append(
                        MenuOption(fname, color=self.dir_color, filetype=ftype)
                    )
        if self.mode != "Delete" and self.mode != "Rename":
            print(f"Mode: {self.mode}")
            if self.create_file_option:
                self.options.append(
                    MenuOption(
                        "New File", color=self.new_file_color, filetype=_TYPE_NEW_FILE
                    )
                )
            if self.create_dir_option:
                self.options.append(
                    MenuOption(
                        "New Dir", color=self.new_dir_color, filetype=_TYPE_NEW_DIR
                    )
                )
            if self.rename_file_option or self.rename_dir_option:
                self.options.append(
                    MenuOption(
                        "Rename",
                        color=self.rename_color,
                        filetype=_TYPE_RENAME,
                    )
                )
            if self.delete_file_option or self.delete_dir_option:
                self.options.append(
                    MenuOption(
                        "Delete",
                        color=self.delete_color,
                        filetype=_TYPE_DELETE,
                    )
                )

        # print(f"Options: {self.options}")

    def refresh_file_contents(self):
        raise NotImplementedError("Override refresh_file_contents in your child class")

    async def make_new_dir(self):
        self.un_setup_buttons()
        name = await TextEntry(self.badge, 16, "Directory name:").get_text()
        if name is not None:
            os.mkdir(name)
        self.setup_buttons()
        self.show(refresh=True)
        # print(name)

    async def make_new_file(self):
        # override this in the child class if the new file shouldn't be completely blank
        self.un_setup_buttons()
        name = await TextEntry(self.badge, 16, "File name:").get_text()
        if name is not None:
            with open(f"{name}.{self.file_extension}", "w") as f:
                pass
            print("made a file :)")
        self.setup_buttons()
        self.show(refresh=True)

    async def delete(self, selection):
        # these shouldn't actually happen
        if not self.delete_dir_option and selection.filetype == _OS_TYPE_DIR:
            print("Check your logic, directories shouldn't be displayed for deletion!")
            return
        elif not self.delete_file_option and selection.filetype == _OS_TYPE_FILE:
            print("Check your logic, files shouldn't be displayed for deletion!")
            return
        self.un_setup_buttons()
        yes_no = YesNoBox(self.badge, "Delete?")
        answer = await yes_no.get_answer()
        if answer:
            print(f"Deleting: {selection.name}")
            # TODO: delete the file or directory
            if selection.filetype == _OS_TYPE_FILE:
                os.remove(selection.name)
            elif selection.filetype == _OS_TYPE_DIR:
                try:
                    os.rmdir(selection.name)
                except OSError as e:
                    error_box = ErrorBox(
                        self.badge,
                        f"Failed to remove {selection.name}: Directory not empty",
                    )
                    await error_box.display_error_async()
            else:
                print(f"Check your logic, just tried to delete {selection.name}")
        self.mode = "Directory"
        self.setup_buttons()
        self.show(refresh=True)

    async def rename(self, selection):
        if not self.rename_dir_option and selection.filetype == _OS_TYPE_DIR:
            return
        if not self.rename_file_option and selection.filetype == _OS_TYPE_FILE:
            return
        print(f"Renaming: {selection.name}")
        self.un_setup_buttons()
        new_name = await TextEntry(self.badge, 16, "File name:").get_text()
        if new_name is not None:
            if selection.filetype == _OS_TYPE_FILE:
                new_name = f"{new_name}.{self.file_extension}"
            if new_name in os.listdir():
                print(f"There is already a file named {new_name}")
                error_box = ErrorBox(
                    self.badge,
                    f"Failed to rename: there is already a file named {new_name}",
                )
                await error_box.display_error_async()
            else:
                os.rename(selection.name, new_name)
        self.mode = "Directory"
        self.setup_buttons()
        self.show(refresh=True)


_OS_TYPE_FILE = 0x8000
_OS_TYPE_DIR = 0x4000
# these numbers are pretty arbitrary, could be changed if they cause a problem
_TYPE_NEW_FILE = 0x8001
_TYPE_NEW_DIR = 0x4001
# _TYPE_DELETE_FILE = 0x8002
# _TYPE_DELETE_DIR = 0x4002
_TYPE_DELETE = 0x3000
_TYPE_RENAME = 0x3001
_TYPE_PARENT_DIR = 0x4003
_TYPE_FAVORITES_DIR = 0x4004
