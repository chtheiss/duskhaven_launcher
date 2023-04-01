import pathlib
import shutil
import signal
import time

import requests

import threads
import utils


def fetch_etag(url):
    """
    Fetches the ETag for the given URL.

    Args:
    url (str): The URL to fetch the ETag for.

    Returns:
    str: The ETag for the given URL.
    """
    response = requests.head(url)
    response.raise_for_status()
    return response.headers.get("etag")


def check_etag(url, info, key):
    if key not in info:
        utils.update_key_in_info_file(key, "")
        return False
    if info[key] == fetch_etag(url):
        return True
    return False


def update_file(url, local_filename, info, dest_path=None):
    print(f"Checking {local_filename}...", flush=True)
    if check_etag(url, info, f"{local_filename}-etag"):
        print(f"{local_filename} already up-to-date", flush=True)
    else:
        print(f"{local_filename} outdated or does not exist.")
        download_file(url, local_filename, dest_path)


def download_file(url, local_filename, dest_path=None):
    """
    Downloads a file from the given URL and saves it to the local file system.

    Args:
    url (str): The URL to download the file from.
    local_filename (str): The path to save the downloaded file to.

    Returns:
    None
    """
    if dest_path is None:
        dest_path = pathlib.Path(local_filename)
    # Download the file
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))
        download_start_time = time.time()
        progress_thread = threads.ProgessTrackThread(
            dest_path, download_start_time, total_size
        )
        signal_handler = utils.SignalHandler(progress_thread)
        signal.signal(signal.SIGINT, signal_handler)

        progress_thread.start()
        print(f"Start downloading {local_filename}", flush=True)
        with open(dest_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        etag = fetch_etag(url)
        utils.update_key_in_info_file(f"{local_filename}-etag", etag)
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
