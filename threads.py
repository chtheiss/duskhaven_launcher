import datetime
import threading
import time


class BackgroundThread:
    def __init__(self, *args):
        self.stopped = False
        self.thread = threading.Thread(target=self.run, args=args)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped = True

    def run(self):
        while not self.stopped:
            pass


def format_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if td.days > 0:
        return f"{td.days} days, {hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class ProgessTrackThread(BackgroundThread):
    def __init__(self, file, download_start_time, total_file_size):
        super().__init__(file, download_start_time, total_file_size)

    def run(self, file, download_start_time, total_file_size):
        current_file_size = 0
        while not self.stopped and current_file_size < total_file_size:
            if not file.exists():
                continue
            file_stats = file.stat()
            mod_time = file_stats.st_mtime
            file_size = file_stats.st_size
            if mod_time - download_start_time > 0 and file_size > current_file_size:
                current_file_size = file_size
                time_diff = mod_time - download_start_time
                progress_percent = file_size / total_file_size * 100
                current_file_size_in_mb = current_file_size / 1024 / 1024
                total_file_size_in_mb = total_file_size / 1024 / 1024
                avg_download_speed = current_file_size / time_diff / 1024 / 1024
                time_remaining = format_time(
                    int(
                        (total_file_size_in_mb - current_file_size_in_mb)
                        / avg_download_speed
                    )
                )
                print(
                    f"Progress: {progress_percent:.2f}%",
                    f"({current_file_size_in_mb:.2f}MB/"
                    f"{total_file_size_in_mb:.2f}MB) | "
                    f"Time passed: {time_diff:.2f}s | "
                    f"Speed: {avg_download_speed:.2f}MB/s | "
                    f"Time left: {time_remaining}",
                    flush=True,
                )
            time.sleep(0.5)
