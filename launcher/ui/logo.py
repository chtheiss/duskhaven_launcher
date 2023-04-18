from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget


class Logo(QWidget):
    def __init__(self, basedir, parent=None) -> None:
        super().__init__(parent)
        self._width = parent.width
        self._height = parent.height
        self.parent = parent

        pixmap = QPixmap(basedir / "images" / "wow-logo.png")

        pixmap = pixmap.scaledToWidth(parent.width * 0.2)

        # Set the pixmap and size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # self.setPixmap(pixmap)
        #

        self.setLayout(QHBoxLayout())

        label = QLabel(pixmap=pixmap)
        label.setScaledContents(True)

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(QLabel(), 1)
        self.layout().addWidget(label, 0)
        self.layout().addWidget(QLabel(), 1)

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        """
        self.setGeometry(
            self.parent.width * 0.83,
            value * 0.07,
            self.parent.width * 0.15,
            value * 0.15,
        )
        """
        self._height = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        """
        self.setGeometry(
            value * 0.83,
            self.parent.height * 0.07,
            value * 0.15,
            self.parent.height * 0.15,
        )
        """
        self._width = value
