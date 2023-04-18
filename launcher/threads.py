import datetime
import logging
import os
import pathlib
import shutil
import time

import requests
from PySide6.QtCore import QObject, QRunnable, QThread, Signal, Slot

from launcher import download, news, server_status, utils

logging.basicConfig(
    filename="launcher.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("Threads")


def format_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if td.days > 0:
        return f"{td.days} days, {hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class NewsSignals(QObject):
    news = Signal(list)
    changelog = Signal(list)
    launcher_news = Signal(list)


class NewsTask(QRunnable):
    def __init__(self, news_type):
        super().__init__()
        self.news_type = news_type
        self.signals = NewsSignals()

    def run(self):
        if self.news_type == "news":
            news_object = news.fetch_announcements()
            news_object = [(n["timestamp"], n["content"]) for n in news_object]
            self.signals.news.emit(news_object)
        elif self.news_type == "changelog":
            news_object = news.fetch_changelog()
            news_object = [(n["timestamp"], n["content"]) for n in news_object]
            self.signals.changelog.emit(news_object)
        elif self.news_type == "launcher-news":
            news_object = news.get_release_notes()
            news_object = [(n["timestamp"], n["content"]) for n in news_object]
            self.signals.launcher_news.emit(news_object)
        else:
            logger.error(
                f"Provided '{self.news_type}' as news type. But news type should "
                "be one of {'news', 'changelog', 'launcher-news'}"
            )


class ServerStatusSignals(QObject):
    login_server_status = Signal(bool)
    game_server_status = Signal(bool)


class ServerStatusTask(QRunnable):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.signals = ServerStatusSignals()

    def run(self):
        if self.server == "game":
            self.signals.game_server_status.emit(server_status.check_game_server())
        elif self.server == "login":
            self.signals.login_server_status.emit(server_status.check_login_server())
        else:
            logger.error(
                f"Provided {self.server} as server name. But server should "
                "be one of {'game', 'login'}"
            )


class InstallWoWTaskSignals(QObject):
    install_finished = Signal(bool)


class InstallWoWTask(QThread):
    def __init__(self, install_folder, wow_client_zip_path, delete_client_zip=False):
        super().__init__()
        self.install_folder = install_folder
        self.wow_client_zip_path = wow_client_zip_path
        self.delete_client_zip = delete_client_zip
        self.install_successful = False
        self.signals = InstallWoWTaskSignals()

    def run(self):
        self.install_successful = utils.prepare_wow_folder(
            self.install_folder, self.wow_client_zip_path, self.delete_client_zip
        )
        logger.info(f"Install successful: {self.install_successful}")
        self.signals.install_finished.emit(self.install_successful)


class BackgroundTaskSignals(QObject):
    progress_update = Signal(int)
    progress_label_update = Signal(str)
    finished_download = Signal(str, str)
    finished_launcher_download = Signal(str)
    update_config = Signal(str, str)
    failed_download = Signal()


class BackgroundTask(QThread):
    def __init__(self, url, dest_path, settings, paused_download_etag=None):
        super().__init__()
        self.paused = False
        self._url = url
        self.dest_path = dest_path
        self.total_size = None
        self.etag = download.fetch_etag(url)
        self.paused_download_etag = paused_download_etag
        self.signals = BackgroundTaskSignals()
        self.stop_flag = False
        self.settings = settings

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value
        self.etag = download.fetch_etag(value)

    def prepare_download(self):
        self.temp_dest_path = pathlib.Path(f"{self.dest_path}.part")

        if not self.temp_dest_path.exists():
            self.temp_dest_path.parent.mkdir(parents=True, exist_ok=True)

        self.download_path = self.temp_dest_path or self.dest_path
        self.total_size = self.total_size or download.fetch_size(self.url)
        self.headers = {}
        if self.download_path.exists():
            file_size = os.path.getsize(self.download_path)
            self.headers = {"Range": f"bytes={file_size}-{self.total_size}"}
            self.mode = "ab"
        else:
            self.mode = "wb"

    @Slot()
    def run(self):
        self.prepare_download()
        self.delete_temp_on_updated_etag()

        with requests.get(self.url, headers=self.headers, stream=True) as response:
            response.raise_for_status()
            self.download_start_time = time.time()
            self.start_file_size = (
                self.download_path.stat().st_size if self.download_path.exists() else 0
            )
            self.current_file_size = self.start_file_size

            with open(self.download_path, self.mode) as file:
                while not self.stop_flag:
                    chunk_start_time = time.time()
                    chunk = response.raw.read(8192)
                    chunk_end_time = time.time()
                    chunk_time = chunk_end_time - chunk_start_time
                    if not chunk:
                        break
                    if self.paused:
                        while self.paused and not self.stop_flag:
                            self.msleep(100)
                            if self.stop_flag:
                                break
                    if chunk:
                        file.write(chunk)
                        bandwidth_limit = self.settings.get("bandwidth", 0)
                        if bandwidth_limit > 0 and chunk_time < (
                            8192 / (bandwidth_limit * 1024)
                        ):
                            wait_time = 8192 / (bandwidth_limit * 1024) - chunk_time
                            self.msleep(int(wait_time * 1000))
                        file_stats = self.download_path.stat()
                        mod_time = file_stats.st_mtime
                        file_size = file_stats.st_size
                        self.current_file_size = file_size
                        time_diff = mod_time - self.download_start_time
                        progress_percent = file_size / self.total_size * 100
                        current_file_size_in_mb = self.current_file_size / 1024 / 1024
                        total_size_in_mb = self.total_size / 1024 / 1024
                        downloaded_size = self.current_file_size - self.start_file_size
                        avg_download_speed = (
                            downloaded_size / (time_diff + 1e-5) / 1024 / 1024
                        )
                        time_remaining = format_time(
                            int(
                                (total_size_in_mb - current_file_size_in_mb)
                                / (avg_download_speed + 1e-5)
                            )
                        )
                        self.signals.progress_label_update.emit(
                            f"Progress: {progress_percent:.2f}% "
                            f"({current_file_size_in_mb:.2f}MB/"
                            f"{total_size_in_mb:.2f}MB) | "
                            f"Time passed: {time_diff:.2f}s | "
                            f"Speed: {avg_download_speed:.2f}MB/s | "
                            f"Time left: {time_remaining}"
                        )
                        self.signals.progress_update.emit(progress_percent)

                if self.stop_flag:
                    logger.info("Stopping download thread.")
                    return

        file_size = os.path.getsize(self.download_path)
        if file_size < self.total_size:
            logger.warning(
                "Restarting download threat! This will NOT cause data loss! "
                "This is most likely because your network connection "
                "got interrupted"
            )
            return self.signals.failed_download.emit()

        self.signals.progress_label_update.emit("100%")
        self.signals.progress_update.emit(100.0)

        if self.download_path is not None:
            shutil.move(self.download_path, self.dest_path)

        etag = download.fetch_etag(self.url)

        if self.etag is None:
            logger.info("Launcher download finished.")
            self.signals.finished_launcher_download.emit(str(self.dest_path))
        else:
            logger.info(f"{self.dest_path} download finished.")
            self.signals.finished_download.emit(str(self.dest_path), etag)

    def pause(self):
        self.paused = True
        self.signals.update_config.emit("paused_download_etag", self.etag)

    def delete_temp(self):
        if self.download_path.exists():
            os.remove(self.download_path)

    def delete_temp_on_updated_etag(self):
        if (
            self.paused_download_etag is not None
            and self.paused_download_etag != self.etag
        ):
            self.delete_temp()

    def resume(self, etag):
        self.paused_download_etag = etag
        self.download_start_time = time.time()
        if hasattr(self, "temp_dest_path"):
            self.delete_temp_on_updated_etag()
            self.start_file_size = (
                self.temp_dest_path.stat().st_size
                if self.temp_dest_path.exists()
                else 0
            )
            self.current_file_size = self.start_file_size
        self.paused = False

    def quit(self):
        self.signals.update_config.emit("paused_download_etag", self.etag)
        self.stop_flag = True
