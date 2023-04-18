from PySide6.QtGui import QColor, QPalette, QPixmap, Qt
from PySide6.QtWidgets import QLabel


class Background(QLabel):
    def __init__(self, basedir, parent=None) -> None:
        super().__init__(parent)
        self._width = parent.width
        self._height = parent.height
        self.setGeometry(0, 0, parent.width, parent.height)
        self.setScaledContents(True)
        pixmap = QPixmap(basedir / "images" / "background.jpg")

        self.setPixmap(pixmap)
        self.setAlignment(Qt.AlignCenter)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))
        self.setPalette(palette)

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self.setGeometry(0, 0, self.width, value)
        self._height = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self.setGeometry(0, 0, value, self.height)
        self._width = value
