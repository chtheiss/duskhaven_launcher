import pathlib
import signal
import tempfile
import time

import requests

import threads
import utils


def download_mega_file(mega, url, dest_path, dest_filename):
    download_start_time = time.time()
    file_handle = mega.get_public_url_info(url)
    total_file_size = int(file_handle["size"])
    dest_file = pathlib.Path(dest_path) / dest_filename
    if dest_file.is_file():
        file_stats = dest_file.stat()
        local_file_size = file_stats.st_size
        if local_file_size == total_file_size:
            print(f"Skipping {dest_file} because it is already up-to-date.", flush=True)
            return
    tempfiles = pathlib.Path(tempfile.gettempdir()).glob("megapy_*")
    progress_thread = threads.ProgessTrackThread(
        tempfiles, download_start_time, total_file_size
    )
    signal_handler = utils.SignalHandler(progress_thread)
    signal.signal(signal.SIGINT, signal_handler)

    progress_thread.start()

    print(f"Start downloading {dest_file}", flush=True)
    mega.download_url(url, dest_path=dest_path, dest_filename=dest_filename)

    progress_thread.stop()


def download_file(url, local_filename):
    """
    Downloads a file from the given URL and saves it to the local file system.

    Args:
    url (str): The URL to download the file from.
    local_filename (str): The path to save the downloaded file to.

    Returns:
    None
    """
    # Download the file
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))
        download_start_time = time.time()
        progress_thread = threads.ProgessTrackThread(
            [local_filename], download_start_time, total_size
        )
        signal_handler = utils.SignalHandler(progress_thread)
        signal.signal(signal.SIGINT, signal_handler)

        progress_thread.start()
        print(f"Start downloading {local_filename}", flush=True)
        with open(local_filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        progress_thread.stop()


def download_and_prepare_wow_client(
    install_folder, wow_client_link_info, wow_exe_link_info
):
    wow_client_zip_file = "wow.zip"
    wow_client_zip_path = install_folder / wow_client_zip_file
    md5_match = False
    while not md5_match:
        download_file(wow_client_link_info["url"], wow_client_zip_path)
        local_md5_hash = utils.calculate_md5(wow_client_zip_path)
        if local_md5_hash == wow_client_link_info["md5"]:
            md5_match = True
        else:
            print("File was corrupted during download. Trying again.", flush=True)

    utils.prepare_wow_folder(
        install_folder, wow_client_zip_path, wow_exe_link_info["original_md5"]
    )
