"""
app/main.py

Central Entry Point for HEXAPOD MOTION DIGITAL TWIN (HEX-01).
Initializes PySide6 Desktop Application and displays the 1600x950 Industrial Workstation.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.ui.main_window import HexapodDigitalTwinMainWindow


def main():
    # Enable High-DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("HEXAPOD MOTION DIGITAL TWIN")
    app.setOrganizationName("HexapodMechatronics")

    window = HexapodDigitalTwinMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
