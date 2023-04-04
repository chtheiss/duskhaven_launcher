import json
import os
import pathlib
import subprocess
import sys

from PySide2 import QtCore
from PySide2.QtGui import QColor, QCursor, QFont, QIcon, QPalette, QPixmap, Qt
from PySide2.QtWidgets import (
    QApplication,
    QDesktopWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

import download
import threads
import utils
from config import Config

basedir = os.path.dirname(__file__)


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window title and size
        self.setWindowTitle("Game Launcher")
        self.setMinimumSize(400, 300)
        self._width, self._height = self.adjust_size()
        self.create_background()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        # Load configuration
        self.load_configuration()

        self.task = threads.BackgroundTask()
        self.task.progress_update.connect(self.update_progress)
        self.task.progress_label_update.connect(self.update_progress_label)
        self.task.finished_download.connect(self.download_next_or_stop)
        self.task.start()

        # Create a font and set it as the label's font
        self.font = QFont()
        self.font.setPointSize(12)  # Set an initial font size

        # Create layouts
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        button_layout = QHBoxLayout()
        top_bar_layout = QHBoxLayout()

        self.create_top_bar(top_bar_layout)

        button_layout.setContentsMargins(0, 10, 0, 0)

        # Create widgets
        self.progress_bar_label = QLabel("")
        self.progress_bar_label.setObjectName("progress_label")
        self.progress_bar_label.setMinimumHeight(self.height * 0.05)
        self.progress_bar_label.setFont(self.font)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress")
        self.progress_bar.setRange(0, 10000)
        self.create_start_button()

        # Add widgets to layouts
        self.create_installation_dialog(main_layout)
        button_layout.addWidget(self.progress_bar)
        button_layout.addWidget(self.start_button)
        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addLayout(top_bar_layout)
        main_layout.addItem(spacer)
        main_layout.addWidget(self.progress_bar_label)
        main_layout.addLayout(button_layout)

        # Set main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Connect signals to slots

        # Set stylesheet
        self.setStyleSheet(
            """
            QLabel#progress_label {
            color: white!important;
            margin-top: 0px;
            margin-bottom: 10px;
            margin-left: 40px;
            margin-right: 20px;
        }
        QLabel#official_site_link a {
            color: white!important;
        }


        QProgressBar#progress {
            background-color: #444444;
            margin-left: 40px;
            margin-right: 40px;
        }

        QProgressBar#progress::chunk {
            background-color: #0078d7;
        }

        QPushButton#start {
            color: white;
            background-color: #0078d7;
            margin-right: 10px;
            margin-left: 30px;
            border-radius: 0px;
            border: 0
        }

        QPushButton#start:hover {
            background-color: #0063ad;
        }

        QLabel#installation_path_label {
            font-size: 16px;
            color: white!important;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        QLineEdit#installation_path_text {
            font-size: 30px;
            color: white;
            border: none;
            padding: 5px;
            border-radius: 5px;
        }

        QPushButton#browse {
            height: 30px;
            font-size: 30px;
            color: white;
            background-color: #0078d7;
            border-radius: 5px;
            margin-left: 10px;
        }

        QPushButton#browse:hover {
            background-color: #0063ad;
        }
        """
        )

    def create_top_bar(self, layout):
        self.official_site_link = QLabel(
            "<a style='color:white; text-decoration: none;' "
            "href='https://duskhaven.servegame.com/'>Official Site</a>"
        )
        self.official_site_link.setObjectName("official_site_link")
        self.official_site_link.setCursor(QCursor(Qt.PointingHandCursor))
        self.official_site_link.setOpenExternalLinks(True)
        self.official_site_link.setFont(self.font)
        layout.addWidget(self.official_site_link)

        self.discord_site_link = QLabel(
            "<a style='color:white; text-decoration: none;' "
            "href='https://discord.gg/duskhaven'>Discord</a>"
        )
        self.discord_site_link.setObjectName("discord_site_link")
        self.discord_site_link.setCursor(QCursor(Qt.PointingHandCursor))
        self.discord_site_link.setOpenExternalLinks(True)
        self.discord_site_link.setFont(self.font)
        layout.addWidget(self.discord_site_link)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer)

        self.quit_button = QPushButton(self)
        self.quit_button.setGeometry(
            self.width * 0.94, self.height * 0.01, self.width * 0.02, self.width * 0.02
        )
        self.quit_button.setAutoFillBackground(False)
        self.quit_button.setText("")
        self.quit_button.setObjectName("close")
        self.quit_button.setIcon(QIcon("images/icons8-close-button-64.png"))
        self.quit_button.setIconSize(QtCore.QSize(self.width * 0.02, self.width * 0.02))
        self.quit_button.setFlat(True)
        self.quit_button.clicked.connect(self.quit_game)
        button_style = """
            QPushButton#close {
                background-color: rgba(0, 0, 0, 0);
                background-color: transparent;
                border: none;
            }
            QPushButton#close:focus {
                background-color: rgba(0, 0, 0, 0);
                background-color: transparent;
                border: none;
            }
            QPushButton#close::icon {
                margin-right: 0px;
                color: white;
            }
        """

        self.quit_button.setCursor(Qt.PointingHandCursor)
        self.quit_button.setStyleSheet(button_style)
        layout.addWidget(self.quit_button)

        layout.setSpacing(20)

    def create_background(self):
        self.background = QLabel(self)
        self.background.setGeometry(0, 0, self.width, self.height)
        self.background.setScaledContents(True)
        pixmap = QPixmap(os.path.join(basedir, "images", "background.png"))
        cropped_pixmap = pixmap.copy(0, 150, pixmap.width(), pixmap.height() - 150)

        self.background.setPixmap(cropped_pixmap)
        self.background.setAlignment(Qt.AlignCenter)
        self.background.mouseMoveEvent = self.mouseMoveEvent

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))
        self.setPalette(palette)

    def create_start_button(self):
        if not hasattr(self, "start_button"):
            self.start_button = QPushButton("Start")
            self.start_button.setObjectName("start")
            self.start_button.setMinimumHeight(self.height * 0.07)
            self.start_button.setMinimumWidth(self.width * 0.2)
            self.start_button.setCursor(QCursor(Qt.PointingHandCursor))
            self.start_button.setFont(self.font)
        if self.check_first_time_user():
            self.start_button.setText("INSTALL")
            self.start_button.clicked.connect(self.install_game)
            return
        elif self.configuration.get("install_in_progress", False):
            self.start_button.setText("RESUME")
            self.start_button.clicked.connect(self.install_game)
            return
        install_folder = pathlib.Path(self.configuration["installation_path"])
        dest_paths = [
            install_folder / "wow.exe",
            install_folder / "Data" / "patch-5.MPQ",
            install_folder / "Data" / "patch-A.MPQ",
            install_folder / "Data" / "patch-Z.mpq",
        ]
        for dest_path in dest_paths:
            file = str(dest_path.name)
            if dest_path.parent.name == "Data":
                full_file = f"Data/{file}"
            else:
                full_file = file
            url = Config.LINKS[full_file]
            if (
                download.file_requires_update(
                    url, dest_path, self.configuration["file_versions"].get(file, "")
                )
                and full_file not in self.configuration["download_queue"]
            ):
                self.configuration["download_queue"].append(full_file)
                self.save_configuration()
        if self.configuration["download_queue"]:
            self.start_button.setText("UPDATE")
            self.start_button.clicked.connect(self.update_game)
        else:
            self.start_button.setText("PLAY")
            self.start_button.clicked.connect(self.start_game)

    def create_installation_dialog(self, main_layout):
        if self.check_first_time_user():
            self.configuration["download_queue"] = list(Config.LINKS.keys())
            self.save_configuration()
            self.installation_path_label = QLabel("Installation Path:")
            self.installation_path_text = QLineEdit()
            self.installation_path_text.setText(
                self.configuration.get(
                    "installation_path", os.path.join(os.getcwd(), "WoW Duskhaven")
                )
            )
            self.installation_path_text.setReadOnly(True)
            self.browse_button = QPushButton("Browse")
            self.browse_button.setObjectName("browse")

            installation_path_layout = QHBoxLayout()
            installation_path_layout.addWidget(self.installation_path_label)
            installation_path_layout.addWidget(self.installation_path_text)
            installation_path_layout.addWidget(self.browse_button)
            main_layout.addLayout(installation_path_layout)
            self.browse_button.clicked.connect(self.show_installation_dialog)

    def update_game(self):
        if self.task.paused:
            self.start_button.setText("PAUSE")
            file = self.configuration["download_queue"][0]
            self.task.url = Config.LINKS[file]
            self.task.resume(
                pathlib.Path(self.configuration["installation_path"]) / file
            )
        else:
            self.start_button.setText("RESUME")
            self.task.pause()

    def start_game(self):
        subprocess.Popen(
            [pathlib.Path(self.configuration["installation_path"]) / "wow.exe"]
        )
        sys.exit(0)

    def install_game(self):
        # Did not attempt to install yet and user clicked install
        dest_path = self.configuration["download_queue"][0]
        if hasattr(self, "installation_path_text"):
            install_folder = self.installation_path_text.text()
        else:
            install_folder = self.configuration["installation_path"]
        if dest_path == "wow-client.zip" and utils.check_wow_install(
            pathlib.Path(install_folder)
        ):
            self.browse_button.setVisible(False)
            self.installation_path_label.setVisible(False)
            self.installation_path_text.setVisible(False)
            self.configuration["download_queue"].pop(0)
            self.configuration["installation_path"] = self.installation_path_text.text()
            self.configuration["install_in_progress"] = False
            self.configuration["file_versions"] = {}
            self.save_configuration()
            self.create_start_button()
            return
        self.task.url = Config.LINKS[dest_path]
        if (
            not self.configuration.get("install_in_progress", False)
            and self.task.paused
        ):
            self.browse_button.setVisible(False)
            self.installation_path_label.setVisible(False)
            self.installation_path_text.setVisible(False)
            self.start_button.setText("PAUSE")
            self.configuration["installation_path"] = self.installation_path_text.text()
            self.save_configuration()

            install_folder = pathlib.Path(self.configuration["installation_path"])
            install_folder.mkdir(parents=True, exist_ok=True)
            self.configuration["install_in_progress"] = True
            self.save_configuration()

            self.task.resume(
                pathlib.Path(self.configuration["installation_path"]) / dest_path
            )
        # Installation in progress and user clicked Resume
        elif self.task.paused:
            self.start_button.setText("PAUSE")
            self.task.resume(
                pathlib.Path(self.configuration["installation_path"]) / dest_path
            )
        else:
            self.start_button.setText("RESUME")
            self.task.pause()

    def quit_game(self):
        # Save configuration and quit the application
        self.save_configuration()
        QApplication.quit()

    def adjust_size(self):
        # Set the size and position of the launcher based on the
        # size and resolution of the screen
        screen = QDesktopWidget().screenGeometry()
        width = screen.width() * 0.5
        height = screen.height() * 0.5
        x = (screen.width() - width) / 2
        y = (screen.height() - height) / 2
        self.setGeometry(x, y, width, height)
        return width, height

    def resizeEvent(self, event):
        # Adjust the size and position of the launcher when the window is resized
        super().resizeEvent(event)
        self.height = event.size().height()
        self.width = event.size().width()
        # self.adjust_size()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self.background.setGeometry(0, 0, self.width, value)
        self._height = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self.background.setGeometry(0, 0, value, self.height)
        self._width = value

    def check_first_time_user(self):
        # Check if this is the first time the user has run the launcher
        return not self.configuration.get("installation_path")

    def show_installation_dialog(self):
        # Prompt the user to select the installation path
        selected_directory = QFileDialog.getExistingDirectory(
            self, "Select Game Installation Path"
        )
        if selected_directory:
            self.configuration["installation_path"] = selected_directory
            self.installation_path_text.setText(selected_directory)
            self.save_configuration()

    def download_next_or_stop(self, dest_path, etag):
        # Download the next file in the queue or stop the download
        file_versions = self.configuration.get("file_versions", {})
        file_versions[pathlib.Path(dest_path).name] = etag
        self.configuration["file_versions"] = file_versions

        if pathlib.Path(dest_path).name == "wow-client.zip":
            utils.prepare_wow_folder(
                pathlib.Path(self.configuration["installation_path"]),
                pathlib.Path(dest_path),
            )
        self.save_configuration()

        download_queue = self.configuration.get("download_queue", [])
        self.configuration["download_queue"] = download_queue
        self.configuration["download_queue"].pop(0)
        self.save_configuration()
        if download_queue:
            file = download_queue[0]
            self.task.url = Config.LINKS[file]
            self.task.dest_path = (
                pathlib.Path(self.configuration["installation_path"]) / file
            )
            self.task.start()
        else:
            self.configuration["install_in_progress"] = False
            self.save_configuration()
            self.task.stop()
            self.start_button.clicked.connect(self.start_game)
            self.start_button.setText("PLAY")

    def load_configuration(self):
        # Load the configuration from a JSON file
        self.configuration = {}
        if os.path.exists("config.json"):
            with open("config.json") as f:
                self.configuration = json.load(f)
        else:
            with open("config.json", "w") as f:
                self.configuration = {}
                json.dump(self.configuration, f)

    def save_configuration(self):
        # Save the configuration to a JSON file
        with open("config.json", "w") as f:
            json.dump(self.configuration, f)

    def update_progress_label(self, info):
        self.progress_bar_label.setText(info)

    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage * 100)
        # displaying the decimal value
        self.progress_bar.setFormat("")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec_())
