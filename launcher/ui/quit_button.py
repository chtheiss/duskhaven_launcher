from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton


class QuitButton(QPushButton):
    def __init__(self, icon_path, size, callback):
        super().__init__()

        self.setAutoFillBackground(False)
        self.setText("")
        self.setObjectName("close")
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QtCore.QSize(size, size))
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)

        button_style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 0);
                background-color: transparent;
                border: none;
            }
            QPushButton:focus {
                background-color: rgba(0, 0, 0, 0);
                background-color: transparent;
                border: none;
            }
            QPushButton::icon {
                margin-right: 0px;
                color: white;
            }
        """
        self.setStyleSheet(button_style)
        self.clicked.connect(callback)
