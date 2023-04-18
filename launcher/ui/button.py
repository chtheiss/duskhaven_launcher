from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QPushButton


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
                padding: 15px 30px;
            }

            QPushButton:hover {
                background-color: #0063ad;
            }

            QPushButton:disabled {
                background-color: #8F8F8F;
            }

            QToolTip {
                color: #ffffff;
                background-color:
                #8F8F8F;
                border: none;
                padding: 2px;
            }
        """
        self.setStyleSheet(style)
        self.setCursor(QCursor(Qt.PointingHandCursor))
