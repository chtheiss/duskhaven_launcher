import logging
import os
import pathlib
import sys

from PySide6 import QtCore
from PySide6.QtGui import QCursor, QIcon, Qt
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QMainWindow,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from launcher import settings, ui, utils

basedir = pathlib.Path(os.path.dirname(__file__))

logging.basicConfig(
    filename="launcher.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("Duskhaven Launcher")


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Starting application")
        # Set window title and size
        self.setWindowTitle("Game Launcher")
        self.setMinimumSize(400, 300)
        self._width, self._height = self.adjust_size()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon(os.path.join(basedir, "images", "favicon.ico")))

        self.configuration = settings.Settings("config.json")

        if self.configuration.get("just_updated", False):
            temp_file = pathlib.Path("temp_launcher")
            if temp_file.exists():
                temp_file.unlink()
            self.configuration["just_updated"] = False
            self.configuration.save()

        # Get the global QThreadPool instance
        self.task = None

        self.main_layout = QGridLayout()

        self.background = ui.Background(basedir, self)
        self.top_bar = ui.TopBar(basedir, self)
        self.logo = ui.Logo(basedir, self)
        self.news_tab = ui.NewsTab(self, self.width * 0.5, self.height * 0.5)
        self.server_status_bar = ui.ServerStatusBar(self)
        self.login = ui.Login(self.width * 0.3, self)
        self.progress_bar = ui.ProgressBar(self)

        self.main_layout.addWidget(self.top_bar, 0, 0, 1, 3)
        self.main_layout.addWidget(self.news_tab, 1, 0, 2, 2)
        self.main_layout.addWidget(self.logo, 1, 2, 1, 1)
        self.main_layout.addWidget(self.server_status_bar, 2, 2, 2, 1)
        self.main_layout.addWidget(self.login, 3, 0, 1, 1)
        self.main_layout.addWidget(self.progress_bar, 4, 0, 1, 2)

        # self.main_layout.setContentsMargins(0, 0, 0, 0)
        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer, 5, 0)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        # latest_version, latest_assets = utils.get_latest_release()
        # if utils.compare_versions(latest_version, version.version) == 1:
        #    logger.info(f"New launcher version available: {latest_version}")
        #    self.update_launcher(latest_assets)

        if "installation_path" in self.configuration:
            utils.add_outdated_files_to_queue(self.configuration)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
            # set cursor to move shape
            self.setCursor(QCursor(Qt.SizeAllCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = None
            event.accept()
            # reset cursor to default
            self.setCursor(Qt.ArrowCursor)

    def adjust_size(self):
        # Set the size and position of the launcher based on the
        # size and resolution of the screen
        screen = self.screen()
        screen_geometry = screen.geometry()

        width = screen_geometry.width() * 0.6
        height = screen_geometry.height() * 0.6
        x = (screen_geometry.width() - width) / 2
        y = (screen_geometry.height() - height) / 2
        self.setGeometry(x, y, width, height)
        return width, height

    def resizeEvent(self, event):
        # Adjust the size and position of the launcher when the window is resized
        super().resizeEvent(event)
        self.height = event.size().height()
        self.width = event.size().width()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self.background.height = value
        self.logo.height = value
        self._height = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self.background.width = value
        self.logo.width = value
        self._width = value


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    """
    try:
        app = QApplication(sys.argv)
        launcher = Launcher()
        launcher.show()
    except Exception as e:
        logging.error(e)
        time.sleep(5)
        sys.exit(1)
    """
    sys.exit(app.exec())
