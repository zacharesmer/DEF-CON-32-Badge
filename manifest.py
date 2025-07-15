# Include the board's default manifest.
include("$(PORT_DIR)/boards/manifest.py")
require("sdcard")
package("pirda")
package("screen")
include("badge.py")
include("main.py")
include()