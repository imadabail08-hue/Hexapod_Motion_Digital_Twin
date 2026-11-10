"""
app/ui/styles.py

Professional Industrial SCADA / Robotics Engineering QSS Dark Theme.
High-contrast technical dark theme with muted grays, cyan accents, and clear status colors.
"""

DARK_INDUSTRIAL_QSS = """
QMainWindow, QDialog {
    background-color: #141416;
    color: #e2e2e5;
    font-family: "Segoe UI", -apple-system, sans-serif;
}

QWidget {
    color: #e2e2e5;
    font-size: 12px;
}

/* Panels & Frames */
QFrame#panelFrame, QGroupBox {
    background-color: #1c1c20;
    border: 1px solid #2e2e34;
    border-radius: 4px;
    padding: 6px;
    margin-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #00bcd4;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* Top Toolbar */
QFrame#topBar {
    background-color: #18181c;
    border-bottom: 1px solid #2e2e34;
    padding: 4px 12px;
}

/* Bottom Action Bar */
QFrame#bottomBar {
    background-color: #18181c;
    border-top: 1px solid #2e2e34;
    padding: 6px 12px;
}

/* Status Badges */
QLabel#badgeOk {
    background-color: #1b5e20;
    color: #81c784;
    border-radius: 3px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 10px;
}

QLabel#badgeWarn {
    background-color: #e65100;
    color: #ffb74d;
    border-radius: 3px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 10px;
}

QLabel#badgeErr {
    background-color: #b71c1c;
    color: #ef9a9a;
    border-radius: 3px;
    padding: 2px 8px;
    font-weight: bold;
    font-size: 10px;
}

QLabel#badgeMode {
    background-color: #004d40;
    color: #80cbc4;
    border-radius: 3px;
    padding: 2px 10px;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* Engineering Buttons */
QPushButton {
    background-color: #26262c;
    border: 1px solid #3d3d46;
    border-radius: 4px;
    color: #e2e2e5;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 11px;
}

QPushButton:hover {
    background-color: #33333c;
    border-color: #00bcd4;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1a1a20;
}

QPushButton#btnEstop {
    background-color: #b71c1c;
    border: 1px solid #ff5252;
    color: #ffffff;
    font-weight: bold;
    font-size: 12px;
    padding: 8px 18px;
}

QPushButton#btnEstop:hover {
    background-color: #d32f2f;
}

QPushButton#btnEstopReset {
    background-color: #1b5e20;
    border: 1px solid #4caf50;
    color: #ffffff;
    font-weight: bold;
}

/* Numerical Readouts */
QLabel#numReadoutLarge {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 20px;
    font-weight: bold;
    color: #00bcd4;
}

QLabel#numReadoutValue {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 13px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#numReadoutMuted {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    color: #8c8c96;
}

/* ScrollBars */
QScrollBar:vertical {
    background-color: #141416;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #2e2e34;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #00bcd4;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Progress bars */
QProgressBar {
    border: 1px solid #2e2e34;
    border-radius: 3px;
    background-color: #141416;
    text-align: center;
    color: #ffffff;
    font-size: 10px;
}

QProgressBar::chunk {
    background-color: #e65100;
    border-radius: 2px;
}
"""
