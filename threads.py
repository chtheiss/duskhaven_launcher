import datetime
import os
import pathlib
import shutil
import time

import requests
from PySide2.QtCore import QThread, Signal

import download


def format_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if td.days > 0:
        return f"{td.days} days, {hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class BackgroundTask(QThread):
    progress_update = Signal(int)
    progress_label_update = Signal(str)
    finished_download = Signal(str, str)
    finished_launcher_download = Signal()

    def __init__(self, url=None):
        super().__init__()
        self.paused = True
        self.dest_path = None
        self.url = url
        self.total_size = None

    def run(self):
        if self.paused:
            while self.paused:
                self.msleep(100)

        temp_dest_path = pathlib.Path(f"{self.dest_path}.part")

        if not temp_dest_path.exists():
            temp_dest_path.parent.mkdir(parents=True, exist_ok=True)

        download_path = temp_dest_path or self.dest_path
        total_size = self.total_size or download.fetch_size(self.url)
        headers = {}
        if download_path.exists():
            file_size = os.path.getsize(download_path)
            headers = {"Range": f"bytes={file_size}-{total_size}"}
            mode = "ab"
        else:
            mode = "wb"

        with requests.get(self.url, headers=headers, stream=True) as response:
            response.raise_for_status()
            download_start_time = time.time()
            start_file_size = (
                temp_dest_path.stat().st_size if temp_dest_path.exists() else 0
            )
            current_file_size = start_file_size

            with open(download_path, mode) as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.paused:
                        while self.paused:
                            self.msleep(100)
                    if chunk:
                        file.write(chunk)
                        file_stats = temp_dest_path.stat()
                        mod_time = file_stats.st_mtime
                        file_size = file_stats.st_size
                        current_file_size = file_size
                        time_diff = mod_time - download_start_time
                        progress_percent = file_size / total_size * 100
                        current_file_size_in_mb = current_file_size / 1024 / 1024
                        total_size_in_mb = total_size / 1024 / 1024
                        downloaded_size = current_file_size - start_file_size
                        avg_download_speed = (
                            downloaded_size / (time_diff + 1e-5) / 1024 / 1024
                        )
                        time_remaining = format_time(
                            int(
                                (total_size_in_mb - current_file_size_in_mb)
                                / (avg_download_speed + 1e-5)
                            )
                        )
                        self.progress_label_update.emit(
                            f"Progress: {progress_percent:.2f}% "
                            f"({current_file_size_in_mb:.2f}MB/"
                            f"{total_size_in_mb:.2f}MB) | "
                            f"Time passed: {time_diff:.2f}s | "
                            f"Speed: {avg_download_speed:.2f}MB/s | "
                            f"Time left: {time_remaining}"
                        )
                        self.progress_update.emit(progress_percent)

        if temp_dest_path is not None:
            shutil.move(temp_dest_path, self.dest_path)

        etag = download.fetch_etag(self.url)

        if self.total_size:
            self.finished_launcher_download.emit()
            self.total_size = None
        else:
            self.finished_download.emit(str(self.dest_path), etag)

    def pause(self):
        self.paused = True

    def resume(self, dest_path):
        self.paused = False
        self.dest_path = dest_path

    def stop(self):
        self.quit()
        self.wait()
