import logging
import os
import pathlib
import subprocess
import sys
import time
from typing import Optional

from PySide6 import QtCore
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCursor, QIcon, Qt
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QMainWindow,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from launcher import credentials, settings, threads, ui, utils, version
from launcher.config import Config

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
        self.progress_bar.hide()
        self.create_start_button()

        self.main_layout.addWidget(self.top_bar, 0, 0, 1, 3)
        self.main_layout.addWidget(self.news_tab, 1, 0, 2, 2)
        self.main_layout.addWidget(self.logo, 1, 2, 1, 1)
        self.main_layout.addWidget(self.server_status_bar, 2, 2, 2, 1)
        self.main_layout.addWidget(self.login, 3, 0, 1, 1)
        if utils.check_first_time_user(self.configuration):
            self.installation_dialog = ui.InstallationDialog(self)
            self.main_layout.addWidget(self.installation_dialog, 4, 0, 1, 3)
            self.main_layout.addWidget(self.start_button, 5, 2, 1, 1)
        else:
            self.main_layout.addWidget(self.progress_bar, 4, 0, 1, 2)
            self.progress_bar.show()
            self.main_layout.addWidget(self.start_button, 4, 2, 1, 1)

        spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer, 5, 0)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        latest_version, latest_assets = utils.get_latest_release()
        if utils.compare_versions(latest_version, version.version) == 1:
            logger.info(f"New launcher version available: {latest_version}")
            self.update_launcher(latest_assets)

        if "installation_path" in self.configuration:
            utils.add_outdated_files_to_queue(self.configuration)

    def create_start_button(self):
        if not hasattr(self, "start_button"):
            self.start_button = ui.Button(self, "", None)
            self.set_start_button_text("PLAY")

        if utils.check_first_time_user(self.configuration):
            logger.info("Setting interaction button to INSTALL")
            self.set_start_button_text("INSTALL")
            self.start_button.clicked.connect(self.start_install_game)
        elif self.configuration.get("install_in_progress", False):
            logger.info("Setting interaction button to RESUME INSTALL")
            self.set_start_button_text("RESUME INSTALL")
            self.start_button.clicked.connect(self.download_client)
        elif self.configuration.get("download_queue"):
            logger.info("Setting interaction button to UPDATE")
            self.set_start_button_text("UPDATE")
            self.start_button.clicked.connect(self.update_game)
        else:
            logger.info("Setting interaction button to PLAY")
            self.set_start_button_text("PLAY")
            self.start_button.clicked.connect(self.start_game)
            self.progress_bar.progress_bar_label.autoplay.set_autoplay()

    def start_install_game(self):
        logger.info("Start install game")
        if hasattr(self, "installation_dialog"):
            self.window().main_layout.removeWidget(self.installation_dialog)
            self.configuration[
                "installation_path"
            ] = self.installation_dialog.installation_path_text.text()
            self.configuration.save()
            self.installation_dialog.deleteLater()
            self.main_layout.addWidget(self.progress_bar, 4, 0, 1, 2)
            self.progress_bar.show()
            self.main_layout.addWidget(self.start_button, 4, 2, 1, 1)
        # Did not attempt to install yet and user clicked install

        install_folder = self.configuration["installation_path"]

        self.check_wow_install()

        if self.configuration["start_button_state"] == "UPDATE":
            logger.info("Game installed but requires updates.")
            self.set_start_button_text("PAUSE")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.update_game)
            self.download_next_or_stop(None, None)
            return
        if self.configuration["start_button_state"] == "PLAY":
            logger.info("Game already up-to-date.")
            self.set_start_button_text("PLAY")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.start_game)
            return

        download_queue = self.configuration.get("download_queue", [])
        wow_zip_dest_path = pathlib.Path(install_folder) / "wow-client.zip"
        if "wow-client.zip" not in download_queue and not wow_zip_dest_path.exists():
            self.configuration["download_queue"] = ["wow-client.zip"] + download_queue
            self.configuration.save()
        utils.add_outdated_files_to_queue(self.configuration)

        if wow_zip_dest_path.exists():
            self.start_install_task(wow_zip_dest_path)
        else:
            self.download_client()
            self.set_start_button_text("PAUSE")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.pause_install_game)

    def download_client(self):
        logger.info("Download client")
        if not self.task:
            self.set_start_button_text("PAUSE")
            self.configuration["install_in_progress"] = True
            self.configuration.save()
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
                self.set_start_button_text("PLAY")
                self.progress_bar.progress_bar_label.autoplay.set_autoplay()

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
            self.set_start_button_text("PAUSE")
        elif self.task.paused:
            self.set_start_button_text("PAUSE")
            self.task.resume(self.configuration.get("paused_download_etag"))
        else:
            self.set_start_button_text("RESUME")
            self.task.pause()

    def create_runnable(self, *args, **kwargs):
        self.task = threads.BackgroundTask(*args, **kwargs, settings=self.configuration)
        self.task.signals.progress_update.connect(self.progress_bar.update_progress)
        self.task.signals.progress_label_update.connect(
            self.progress_bar.progress_bar_label.update_progress_label
        )
        self.task.signals.finished_download.connect(self.download_next_or_stop)
        self.task.signals.finished_launcher_download.connect(
            self.complete_launcher_update
        )
        self.task.signals.failed_download.connect(self.restart_download_task)
        self.task.signals.update_config.connect(self.update_config)

    def start_install_task(self, dest_path):
        self.number_install_dots = 1
        self.install_label_timer = QTimer()
        self.start_button.setEnabled(False)
        self.set_start_button_text("EXCTRACTING CLIENT")
        self.start_button.clicked.disconnect()
        self.install_label_timer.timeout.connect(self.set_installing_label)
        self.install_label_timer.start(1000)
        self.install_task = threads.InstallWoWTask(
            pathlib.Path(self.configuration["installation_path"]),
            pathlib.Path(dest_path),
            self.configuration.get("delete_client_zip_after_install", False),
        )
        self.install_task.signals.install_finished.connect(self.finish_base_install)
        self.install_task.start()

    def restart_download_task(self):
        logger.info("Restarting download task.")
        self.task = None
        self.update_game()

    def update_config(self, key, value):
        self.configuration[key] = value
        self.configuration.save()

    def set_installing_label(self):
        self.progress_bar.progress_bar_label.update_progress_label(
            f"Installing Base Game {self.number_install_dots * '.'}"
        )
        if self.number_install_dots == 3:
            self.number_install_dots = 0
        self.number_install_dots += 1

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
            self.configuration.save()

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
            self.configuration.save()
            if self.task:
                self.task.quit()
                self.task.wait()
                self.task = None
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.start_game)
            self.set_start_button_text("PLAY")
            self.progress_bar.progress_bar_label.autoplay.set_autoplay()

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
            self.configuration.save()

        if not install_successful:
            self.progress_bar.progress_bar_label.update_progress_label(
                "Installation Failed!"
            )
            return

        self.start_button.setEnabled(True)
        self.start_button.clicked.connect(self.update_game)
        self.update_game()

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
        self.configuration.save()

        time.sleep(2)
        logger.info(f"Starting Launcher: {executable_path}")
        try:
            subprocess.Popen(str(executable_path), shell=True).wait()
        except Exception as e:
            logger.error(e)

        QApplication.quit()

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

    def check_wow_install(self):
        # If WoW already installed -> update or play
        if utils.check_wow_install(
            pathlib.Path(self.configuration["installation_path"])
        ):
            utils.add_outdated_files_to_queue(self.configuration)
            if hasattr(self, "installation_dialog"):
                self.installation_dialog.deleteLater()
                self.main_layout.addWidget(self.progress_bar, 4, 0, 1, 2)
                self.main_layout.addWidget(self.start_button, 4, 2, 1, 1)
                self.progress_bar.show()
            # If any file needs update -> update
            if len(self.configuration["download_queue"]) > 0:
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.update_game)
                self.set_start_button_text("UPDATE")
                status = "UPDATE"
            # All files up-to-date -> play
            else:
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.start_game)
                self.set_start_button_text("PLAY")
                status = "PLAY"
        else:
            status = "INSTALL"

        self.configuration["start_button_state"] = status
        self.configuration.save()
        self.start_button.setEnabled(True)

    def set_start_button_text(self, text):
        self.start_button.setText(text)
        self.configuration["start_button_state"] = text
        self.configuration.save()

    def update_launcher(self, assets):
        if hasattr(self, "browse_button"):
            self.browse_button.setVisible(False)
            self.installation_path_label.setVisible(False)
            self.installation_path_text.setVisible(False)

        self.set_start_button_text("UPDATING LAUNCHER")
        self.start_button.setEnabled(False)
        self.progress_bar.progress_bar_label.autoplay.autoplay.setCheckable(False)
        self.progress_bar.progress_bar_label.autoplay.autoplay.setChecked(False)
        if hasattr(self.progress_bar.progress_bar_label.autoplay, "autoplay_timer"):
            self.progress_bar.progress_bar_label.autoplay.autoplay_timer.stop()

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

    def start_game(self):
        logger.info("Starting game")
        password_ = None
        if self.configuration.get("save_credentials", False):
            password_ = credentials.get_password()
            credentials.update_account_name(
                pathlib.Path(self.configuration["installation_path"])
                / "WTF"
                / "Config.wtf",
                credentials.get_account_name(),
            )

        if sys.platform.startswith("win"):
            subprocess.Popen(
                [pathlib.Path(self.configuration["installation_path"]) / "wow.exe"]
            )
        elif sys.platform.startswith("linux"):
            # if you prefer, these logging lines can be removed
            logger.info("Linux support is in beta")
            logger.info("Wine is required")
            logger.info(
                "Proper prior setup of wine and related environment variables "
                "is highly recommended"
            )
            subprocess.Popen(
                [
                    "wine",
                    pathlib.Path(self.configuration["installation_path"]) / "wow.exe",
                ]
            )
        else:
            logger.error(f"{sys.platform} is completely unsupported!")
            logger.info("Exiting!")

        if password_ is None:
            return QApplication.quit()

        if sys.platform.startswith("linux") or sys.platform.startswith("win"):
            password_wait_timer = self.configuration.get("password_wait_timer")
            if password_wait_timer is None:
                self.configuration.set("password_wait_timer", 5)
                self.configuration.save()
            logger.info(
                "Waiting "
                + str(self.configuration.get("password_wait_timer"))
                + " seconds before trying to enter password"
            )
            time.sleep(self.configuration["password_wait_timer"])
            credentials.type_password(password_)
            # credentials.type_key(Key.enter)

        QApplication.quit()

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
