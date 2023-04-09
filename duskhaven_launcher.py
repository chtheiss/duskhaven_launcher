import json
import logging
import os
import pathlib
import subprocess
import sys
import time
from typing import Optional

from PySide6 import QtCore
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QPalette, QPixmap, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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

logging.basicConfig(
    filename="launcher.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("Duskhaven Launcher")

version = "v0.1.1"


class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Starting application")
        # Set window title and size
        self.setWindowTitle("Game Launcher")
        self.setMinimumSize(400, 300)
        self._width, self._height = self.adjust_size()
        self.create_background()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon(os.path.join(basedir, "images", "favicon.ico")))
        # Load configuration
        self.load_configuration()

        if self.configuration.get("just_updated", False):
            temp_file = pathlib.Path("temp_launcher")
            if temp_file.exists():
                temp_file.unlink()
            self.configuration["just_updated"] = False
            self.save_configuration()

        # Get the global QThreadPool instance
        self.task = None

        # Create a font and set it as the label's font
        self.font = QFont()
        self.font.setPointSize(12)  # Set an initial font size

        self.font_small = QFont()
        self.font_small.setPointSize(8)  # Set an initial font size

        # Create layouts
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.button_layout = QHBoxLayout()
        self.progress_bar_layout = QVBoxLayout()
        self.progress_bar_label_layout = QHBoxLayout()
        top_bar_layout = QHBoxLayout()

        self.create_top_bar(top_bar_layout)

        # Create widgets
        self.progress_bar_label = QLabel("")
        self.progress_bar_label.setObjectName("progress_label")
        self.progress_bar_label.setMinimumHeight(self.height * 0.05)
        self.progress_bar_label.setFont(self.font_small)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress")
        self.progress_bar.setRange(0, 10000)
        self.progress_bar.setMaximumHeight(self.height * 0.02)

        self.autoplay_in_label = QLabel("")
        self.progress_bar.setObjectName("autoplay_in_label")
        self.autoplay_in_label.setFont(self.font_small)
        self.autoplay_in_label.setStyleSheet(
            """
            color: white!important;
            margin-right: 5px;
            """
        )

        self.autoplay = QCheckBox()
        self.autoplay.setText("AUTO-PLAY")
        self.autoplay.setFont(self.font_small)
        self.autoplay.setObjectName("autoplay")
        self.autoplay.setLayoutDirection(Qt.RightToLeft)
        self.autoplay.setChecked(self.configuration.get("autoplay", False))
        self.autoplay.toggled.connect(self.set_autoplay)

        self.progress_bar_label_layout.addWidget(self.progress_bar_label)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.progress_bar_label_layout.addItem(spacer)
        self.progress_bar_label_layout.addWidget(self.autoplay_in_label)
        self.progress_bar_label_layout.addWidget(self.autoplay)
        self.progress_bar_label_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_bar_layout.addLayout(self.progress_bar_label_layout)
        self.progress_bar_layout.addWidget(self.progress_bar)

        if "installation_path" in self.configuration:
            self.add_outdated_files_to_queue()
        self.create_start_button()
        # Add widgets to layouts
        self.button_layout.addLayout(self.progress_bar_layout)
        self.button_layout.addWidget(self.start_button)
        self.main_layout.addLayout(top_bar_layout)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer)
        dialog_created = self.create_installation_dialog()
        if not dialog_created:
            self.button_layout.setContentsMargins(0, 0, 0, self.height * 0.01)
        else:
            self.button_layout.setContentsMargins(0, 10, 0, self.height * 0.01)

        self.main_layout.addLayout(self.button_layout)

        if self.start_button.text() == "PLAY":
            self.progress_bar.setValue(100 * 100)
            self.progress_bar.setFormat("")
            self.progress_bar_label.setText("100%")

        # Set main layout
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        latest_version, latest_assets = utils.get_latest_release()
        if utils.compare_versions(latest_version, version) == 1:
            logger.info(f"New launcher version available: {latest_version}")
            self.update_launcher(latest_assets)

        # Connect signals to slots

        # Set stylesheet
        self.setStyleSheet(
            """
            QLabel#progress_label {
            color: white!important;
            margin-top: 0px;
            margin-left: 40px;

        }

        QCheckBox#autoplay {
            color: white!important;
            margin-right: 5px;
        }

        QProgressBar {
            background-color: #444444!important;
            margin-left: 40px;
            margin-right: 5px;
        }

        QProgressBar::chunk {
            background-color: #0078d7!important;
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
            color: white;
        }

        QLineEdit#installation_path_text {
            color: white;
            border: none;
            margin-left: 40px;
            margin-right: 40px;
        }

        QPushButton#browse {
            color: white;
            background-color: #0078d7;
            margin-right: 10px;
            margin-left: 30px;
            border-radius: 0px;
            border: 0;
        }

        QPushButton#browse:hover {
            background-color: #0063ad;
        }
        """
        )

    def set_autoplay(self):
        if self.autoplay.isChecked():
            self.configuration["autoplay"] = True
            self.save_configuration()
            if self.start_button.text() == "PLAY":
                self.remaining_seconds = 5  # set the initial value of remaining seconds
                self.autoplay_timer = QTimer()
                self.autoplay_timer.timeout.connect(
                    self.update_countdown_label
                )  # connect the timer to the update_countdown_label method
                self.autoplay_in_label.setText(f"{self.remaining_seconds} seconds")
                self.autoplay_timer.start(
                    1000
                )  # start the timer to fire every 1000ms (1 second)
        else:
            self.configuration["autoplay"] = False
            if hasattr(self, "autoplay_timer"):
                self.autoplay_timer.stop()
                self.autoplay_in_label.setText("")
            self.save_configuration()

    def set_installing_label(self):
        self.progress_bar_label.setText(
            f"Installing Base Game {self.number_install_dots * '.'}"
        )
        if self.number_install_dots == 3:
            self.number_install_dots = 0
        self.number_install_dots += 1

    def update_countdown_label(self):
        self.remaining_seconds -= 1  # decrement the remaining seconds
        self.autoplay_in_label.setText(
            f"{self.remaining_seconds} seconds"
        )  # update the label text
        if self.remaining_seconds == 0:
            self.autoplay_timer.stop()  # stop the timer when the countdown is over
            self.autoplay_in_label.setText("")
            self.start_game()

    def update_config(self, key, value):
        self.configuration[key] = value
        self.save_configuration()

    def create_top_bar(self, layout):
        self.official_site_link = QLabel(
            "<a style='color:white; text-decoration: none; font-weight:500' "
            "href='https://duskhaven.servegame.com/'>OFFICIAL SITE</a>"
        )
        self.official_site_link.setObjectName("official_site_link")
        self.official_site_link.setCursor(QCursor(Qt.PointingHandCursor))
        self.official_site_link.setOpenExternalLinks(True)
        self.official_site_link.setFont(self.font)
        layout.addWidget(self.official_site_link)

        self.register_site_link = QLabel(
            "<a style='color:white; text-decoration: none; font-weight:500' "
            "href='https://duskhaven.servegame.com/account/register/'>REGISTER</a>"
        )
        self.register_site_link.setObjectName("register_site_link")
        self.register_site_link.setCursor(QCursor(Qt.PointingHandCursor))
        self.register_site_link.setOpenExternalLinks(True)
        self.register_site_link.setFont(self.font)
        layout.addWidget(self.register_site_link)

        self.discord_site_link = QLabel(
            "<a style='color:white; text-decoration: none; font-weight:500' "
            "href='https://discord.gg/duskhaven'>DISCORD</a>"
        )
        self.discord_site_link.setObjectName("discord_site_link")
        self.discord_site_link.setCursor(QCursor(Qt.PointingHandCursor))
        self.discord_site_link.setOpenExternalLinks(True)
        self.discord_site_link.setFont(self.font)
        layout.addWidget(self.discord_site_link)

        self.source_code = QLabel(
            "<a style='color:white; text-decoration: none; font-weight:500' "
            "href='https://github.com/chtheiss/duskhaven_launcher'>"
            f"Version {version}</a>"
        )
        self.source_code.setObjectName("source_code")
        self.source_code.setCursor(QCursor(Qt.PointingHandCursor))
        self.source_code.setOpenExternalLinks(True)
        self.source_code.setFont(self.font)
        layout.addWidget(self.source_code)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer)

        self.minimize_button = QPushButton(self)
        self.minimize_button.setGeometry(
            self.width * 1, self.height * 0.01, self.width * 0.04, self.width * 0.02
        )
        self.minimize_button.setAutoFillBackground(False)
        self.minimize_button.setText("")
        self.minimize_button.setObjectName("minimize")
        self.minimize_button.setIcon(
            QIcon(os.path.join(basedir, "images", "icons8-minimize-button-64.png"))
        )
        self.minimize_button.setIconSize(
            QtCore.QSize(self.width * 0.04, self.width * 0.02)
        )
        self.minimize_button.setFlat(True)
        self.minimize_button.clicked.connect(self.minimize_launcher)
        button_style = """
            QPushButton#minimize {
                background-color: rgba(0, 0, 0, 0);
                background-color: transparent;
                border: none;
            }
            QPushButton#minimize:focus {
                background-color: rgba(0, 0, 0, 0);
                background-color: transparent;
                border: none;
            }
            QPushButton#minimize::icon {
                margin-right: 0px;
                color: white;
            }
        """
        self.minimize_button.setCursor(Qt.PointingHandCursor)
        self.minimize_button.setStyleSheet(button_style)
        self.minimize_button.setMaximumHeight(0.015 * self.height)
        layout.addWidget(self.minimize_button)

        self.quit_button = QPushButton(self)
        self.quit_button.setGeometry(
            self.width * 0.94, self.height * 0.01, self.width * 0.02, self.width * 0.02
        )

        self.quit_button.setAutoFillBackground(False)
        self.quit_button.setText("")
        self.quit_button.setObjectName("close")
        self.quit_button.setIcon(
            QIcon(os.path.join(basedir, "images", "icons8-close-button-64.png"))
        )
        self.quit_button.setIconSize(QtCore.QSize(self.width * 0.02, self.width * 0.02))
        self.quit_button.setFlat(True)
        self.quit_button.clicked.connect(self.quit_launcher)
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
            logger.info("Setting interaction button to INSTALL")
            self.start_button.setText("INSTALL")
            self.start_button.clicked.connect(self.start_install_game)
        elif self.configuration.get("install_in_progress", False):
            logger.info("Setting interaction button to RESUME INSTALL")
            self.start_button.setText("RESUME INSTALL")
            self.start_button.clicked.connect(self.download_install_game)
        elif self.configuration.get("download_queue"):
            logger.info("Setting interaction button to UPDATE")
            self.start_button.setText("UPDATE")
            self.start_button.clicked.connect(self.update_game)
        else:
            logger.info("Setting interaction button to PLAY")
            self.start_button.setText("PLAY")
            self.start_button.clicked.connect(self.start_game)
            self.set_autoplay()

    def create_installation_dialog(self):
        if self.check_first_time_user():
            self.installation_path_label = QLabel(
                "<p style='color:white;'>Installation Path: </p>"
            )
            self.installation_path_label.setFont(self.font)
            self.installation_path_text = QLineEdit()
            self.installation_path_text.setText(
                self.configuration.get(
                    "installation_path", os.path.join(os.getcwd(), "WoW Duskhaven")
                )
            )
            self.installation_path_text.setFont(self.font)
            self.installation_path_text.setReadOnly(True)

            self.browse_button = QPushButton("Browse")
            self.browse_button.setObjectName("browse")
            self.browse_button.setMinimumHeight(self.height * 0.07)
            self.browse_button.setMinimumWidth(self.width * 0.2)
            self.browse_button.setCursor(QCursor(Qt.PointingHandCursor))
            self.browse_button.setFont(self.font)

            self.installation_path_layout = QHBoxLayout()
            self.installation_path_layout.addWidget(self.installation_path_label)
            self.installation_path_layout.addWidget(self.installation_path_text)
            self.installation_path_layout.addWidget(self.browse_button)
            self.main_layout.addLayout(self.installation_path_layout)
            self.browse_button.clicked.connect(self.show_installation_dialog)
            return True
        return False

    def update_game(self):
        logger.info("Updating game.")
        if not self.task:
            file = self.configuration["download_queue"][0]
            url = Config.LINKS[file]
            self.create_runnable(
                url=url,
                dest_path=pathlib.Path(self.configuration["installation_path"]) / file,
                paused_download_etag=self.configuration.get("paused_download_etag"),
            )
            self.task.start()
            self.start_button.setText("PAUSE")
        elif self.task.paused:
            self.start_button.setText("PAUSE")
            self.task.resume(self.configuration.get("paused_download_etag"))
        else:
            self.start_button.setText("RESUME")
            self.task.pause()

    def create_runnable(self, *args, **kwargs):
        self.task = threads.BackgroundTask(*args, **kwargs)
        self.task.signals.progress_update.connect(self.update_progress)
        self.task.signals.progress_label_update.connect(self.update_progress_label)
        self.task.signals.finished_download.connect(self.download_next_or_stop)
        self.task.signals.finished_launcher_download.connect(
            self.complete_launcher_update
        )
        self.task.signals.update_config.connect(self.update_config)

    def update_launcher(self, assets):
        if hasattr(self, "browse_button"):
            self.browse_button.setVisible(False)
            self.installation_path_label.setVisible(False)
            self.installation_path_text.setVisible(False)

        self.start_button.setText("UPDATING LAUNCHER")
        self.start_button.setEnabled(False)
        self.autoplay.setCheckable(False)
        self.autoplay.setChecked(False)
        if hasattr(self, "autoplay_timer"):
            self.autoplay_timer.stop()

        if getattr(sys, "frozen", False):
            executable_path = pathlib.Path(sys.executable)
        else:
            executable_path = pathlib.Path(sys.argv[0])

        possible_assets = [
            asset for asset in assets if asset["name"].endswith(executable_path.suffix)
        ]
        if len(possible_assets) == 0:
            logger.warning("Changed file extension!")
        elif len(possible_assets) > 1:
            logger.warning("Found multiple assets")

        asset = possible_assets[0]

        logger.info(
            f"Start downloading {asset['name']} "
            f"from {asset['browser_download_url']}"
        )

        file = asset["name"] + ".new"
        self.create_runnable(
            url=asset["browser_download_url"], dest_path=file, paused_download_etag=None
        )
        self.task.total_size = asset["size"]
        self.task.start()

    def complete_launcher_update(self, new_version_path):
        if getattr(sys, "frozen", False):
            # The application is frozen.
            executable_path = pathlib.Path(sys.executable)
        else:
            # The application is not frozen.
            # We assume the script is being executed from the command line.
            executable_path = pathlib.Path(sys.argv[0])

        logger.info(f"Name of current launcher: {executable_path}")

        new_version_path = pathlib.Path(new_version_path)

        temp_name = "temp_launcher"
        try:
            executable_path.rename(executable_path.parent / temp_name)
            time.sleep(1)
        except Exception as e:
            logger.error(e)
        try:
            new_version_path.rename(executable_path)
            time.sleep(1)
        except Exception as e:
            logger.error(e)

        self.configuration["just_updated"] = True
        self.save_configuration()

        time.sleep(2)
        logger.info(f"Starting Launcher: {executable_path}")
        try:
            subprocess.Popen(str(executable_path), shell=True).wait()
        except Exception as e:
            logger.error(e)
        QApplication.quit()

    def start_game(self):
        logger.info("Starting game")
        if sys.platform.startswith('win'):
            subprocess.Popen([pathlib.Path(self.configuration["installation_path"]) / "wow.exe"])
        elif sys.platform.startswith('linux'):
            # if you prefer, these logging lines can be removed
            logger.info("Linux support is in beta")
            logger.info("Wine is required")
            logger.info("Proper prior setup of wine and related environment variables is highly recommended")
            subprocess.Popen(["wine", pathlib.Path(self.configuration["installation_path"]) / "wow.exe"])
        elif sys.platform.startswith('darwin'):
            # if you prefer, these logging lines can be removed
            logger.info("Mac OSX is unsupported")
            logger.info("Trying anyway...")
            logger.info("Wine is required")
            logger.info("Proper prior setup of wine and related environment variables is highly recommended")
            subprocess.Popen(["wine", pathlib.Path(self.configuration["installation_path"]) / "wow.exe"])
        else:
            logger.info("ERROR: " + sys.platform + " is completely unsupported!")
            logger.info("Exiting!")
            
        QApplication.quit()

    def add_outdated_files_to_queue(self):
        install_folder = pathlib.Path(self.configuration["installation_path"])
        donwload_queue = self.configuration.get("download_queue", [])
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
                    url,
                    dest_path,
                    self.configuration.get("file_versions", {}).get(file, ""),
                )
                and full_file not in donwload_queue
            ):
                donwload_queue.append(full_file)
        self.configuration["download_queue"] = donwload_queue
        self.save_configuration()

    def start_install_game(self):
        logger.info("Start install game")
        if hasattr(self, "browse_button"):
            self.browse_button.setVisible(False)
            self.installation_path_label.setVisible(False)
            self.installation_path_text.setVisible(False)
        # Did not attempt to install yet and user clicked install
        if hasattr(self, "installation_path_text"):
            install_folder = self.installation_path_text.text()
        else:
            install_folder = self.configuration["installation_path"]

        if "installation_path" not in self.configuration:
            self.configuration["installation_path"] = install_folder
            self.save_configuration()

        status = self.check_wow_install()
        if status == "update":
            logger.info("Game installed but requires updates.")
            self.start_button.setText("PAUSE")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.update_game)
            self.download_next_or_stop(None, None)
            return
        if status == "play":
            logger.info("Game already up-to-date.")
            self.start_button.setText("PLAY")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.start_game)
            return

        download_queue = self.configuration.get("download_queue", [])
        wow_zip_dest_path = pathlib.Path(install_folder) / "wow-client.zip"
        if "wow-client.zip" not in download_queue and not wow_zip_dest_path.exists():
            self.configuration["download_queue"] = ["wow-client.zip"] + download_queue
            self.save_configuration()
        self.add_outdated_files_to_queue()

        if wow_zip_dest_path.exists():
            self.start_install_task(wow_zip_dest_path)
        else:
            self.download_install_game()
            self.start_button.setText("PAUSE")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.pause_install_game)

    def pause_install_game(self):
        logger.info("Pause install game")
        self.start_button.setText("RESUME")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.resume_install_game)
        self.task.pause()

    def resume_install_game(self):
        logger.info("Resume install game")
        self.start_button.setText("PAUSE")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.pause_install_game)
        self.task.resume(self.configuration.get("paused_download_etag"))

    def download_install_game(self):
        logger.info("Download install game")
        if not self.task:
            self.start_button.setText("PAUSE")
            self.configuration["install_in_progress"] = True
            self.save_configuration()
            pathlib.Path(self.configuration["installation_path"]).mkdir(
                parents=True, exist_ok=True
            )
            if len(self.configuration["download_queue"]) > 0:
                file = self.configuration["download_queue"][0]
                url = Config.LINKS[file]
                self.create_runnable(
                    url=url,
                    dest_path=pathlib.Path(self.configuration["installation_path"])
                    / file,
                    paused_download_etag=self.configuration.get("paused_download_etag"),
                )
                self.task.start()
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.pause_install_game)
            else:
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.start_game)
                self.start_button.setText("PLAY")
                self.set_autoplay()

    def quit_launcher(self):
        logger.info("Quitting launcher")
        # Save configuration and quit the application
        self.save_configuration()
        if self.task:
            logger.info("Closing remaining tasks.")
            self.task.quit()
            self.task.wait()
            self.task = None
        QApplication.quit()

    def minimize_launcher(self):
        logger.info("Minimizing launcher")
        self.showMinimized()

    def adjust_size(self):
        # Set the size and position of the launcher based on the
        # size and resolution of the screen
        screen = self.screen()
        screen_geometry = screen.geometry()

        width = screen_geometry.width() * 0.5
        height = screen_geometry.height() * 0.5
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

    def check_wow_install(self):
        # If WoW already installed -> update or play
        if utils.check_wow_install(
            pathlib.Path(self.configuration["installation_path"])
        ):
            self.add_outdated_files_to_queue()
            if hasattr(self, "browse_button"):
                self.browse_button.setVisible(False)
                self.installation_path_label.setVisible(False)
                self.installation_path_text.setVisible(False)
            # If any file needs update -> update
            if len(self.configuration["download_queue"]) > 0:
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.update_game)
                self.start_button.setText("UPDATE")
                self.start_button.setEnabled(True)
                return "update"
            # All files up-to-date -> play
            else:
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.start_game)
                self.start_button.setText("PLAY")
                self.start_button.setEnabled(True)
                return "play"

        self.start_button.setEnabled(True)
        return "install"

    def show_installation_dialog(self):
        # Prompt the user to select the installation path
        selected_directory = QFileDialog.getExistingDirectory(
            self, "Select Game Installation Path"
        )
        if selected_directory:
            self.configuration["installation_path"] = selected_directory
            self.installation_path_text.setText(selected_directory)
            self.save_configuration()
            self.start_button.setEnabled(False)
            self.check_wow_install()

    def finish_base_install(self, install_successful):
        if self.task:
            self.task.quit()
            self.task.wait()
            self.task = None
        if self.install_task:
            self.install_task.quit()
            self.install_task.wait()
            self.install_task = None

        if hasattr(self, "install_label_timer"):
            self.install_label_timer.stop()

        download_queue = self.configuration.get("download_queue", [])
        if len(download_queue) > 0 and download_queue[0] == "wow-client.zip":
            self.configuration["download_queue"] = download_queue
            removed_download = self.configuration["download_queue"].pop(0)
            logger.info(f"Removing {removed_download} from download queue.")
            logger.info(f"Download queue: {self.configuration['download_queue']}")
            self.save_configuration()

        if not install_successful:
            self.progress_bar_label.setText("Installation Failed!")
            return

        self.start_button.setEnabled(True)
        self.start_button.clicked.connect(self.update_game)
        self.update_game()

    def start_install_task(self, dest_path):
        self.number_install_dots = 1
        self.install_label_timer = QTimer()
        self.start_button.setEnabled(False)
        self.start_button.setText("EXCTRACTING CLIENT")
        self.start_button.clicked.disconnect()
        self.install_label_timer.timeout.connect(self.set_installing_label)
        self.install_label_timer.start(1000)
        self.install_task = threads.InstallWoWTask(
            pathlib.Path(self.configuration["installation_path"]),
            pathlib.Path(dest_path),
        )
        self.install_task.signals.install_finished.connect(self.finish_base_install)
        self.install_task.start()

    def download_next_or_stop(
        self, dest_path: Optional[str] = None, etag: Optional[str] = None
    ):
        # Download the next file in the queue or stop the download
        if dest_path and etag:
            file_versions = self.configuration.get("file_versions", {})
            file_versions[pathlib.Path(dest_path).name] = etag
            self.configuration["file_versions"] = file_versions
            self.configuration["paused_download_etag"] = None
            removed_download = self.configuration["download_queue"].pop(0)
            logger.info(
                "download_next_or_stop: Removing "
                f"{removed_download} from download queue."
            )
            logger.info(
                "download_next_or_stop: Download queue: "
                f"{self.configuration['download_queue']}"
            )
            self.save_configuration()

        if self.task:
            self.task.quit()
            self.task.wait()
            self.task = None

        if dest_path is not None and pathlib.Path(dest_path).name == "wow-client.zip":
            self.start_install_task(dest_path)
            return

        download_queue = self.configuration.get("download_queue", [])
        if download_queue:
            file = download_queue[0]
            self.create_runnable(
                url=Config.LINKS[file],
                dest_path=pathlib.Path(self.configuration["installation_path"]) / file,
                paused_download_etag=self.configuration.get("paused_download_etag"),
            )
            self.task.start()
        else:
            self.configuration["install_in_progress"] = False
            self.save_configuration()
            if self.task:
                self.task.quit()
                self.task.wait()
                self.task = None
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.start_game)
            self.start_button.setText("PLAY")
            self.set_autoplay()

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
            json.dump(self.configuration, f, indent=2)

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
    # try:
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    # except Exception as e:
    #    logger.error(e)
    # sys.exit(1)
    sys.exit(app.exec())
