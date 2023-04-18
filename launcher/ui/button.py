from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QPushButton

from launcher.ui import fonts


class Button(QPushButton):
    def __init__(self, parent, text, callback=None):
        super().__init__(parent)
        if callback:
            self.clicked.connect(callback)
        self.setText(text)
        style = """
            QPushButton {
                color: white;
                background-color: #0078d7;
                margin-right: 20px;
                margin-left: 20px;
                border-radius: 0px;
                border: 0;
                padding: 12px 25px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0063ad;
            }

            QPushButton:disabled {
                background-color: #8F8F8F;
            }

            QToolTip {
                color: #ffffff;
                background-color: #8F8F8F;
                border: none;
                padding: 2px;
            }
        """
        self.setStyleSheet(style)
        self.setFont(fonts.NORMAL)
        self.setCursor(QCursor(Qt.PointingHandCursor))
