# Include the board's default manifest.
include("$(PORT_DIR)/boards/manifest.py")
# libraries
require("sdcard")
# directories
package("builtin_programs")
package("lib")
package("other_hw")
package("pirda")
package("screen")
# files
module("board_config.py")
module("badge.py")
module("main_menu.py")
module("main.py")
