# Include the board's default manifest.
include("$(PORT_DIR)/boards/manifest.py")
# libraries
require("sdcard")
# directories
package("lib")
package("other_hw")
package("pirda")
package("screen")
# files
module("board_config.py")
module("badge.py")
module("blinkenlights.py")
module("calibrate.py")
module("choose_theme.py")
module("ir_remote.py")
module("main_menu.py")
module("main.py")
module("paint.py")
