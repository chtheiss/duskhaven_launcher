from PySide6.QtGui import QPalette, Qt
from PySide6.QtWidgets import QFrame


def create_divider():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    palette = line.palette()
    palette.setColor(QPalette.WindowText, Qt.white)
    line.setPalette(palette)
    line.setFixedHeight(1)
    line.setStyleSheet(
        """
        QFrame {
            margin: 0px;
        }
        """
    )
    return line
