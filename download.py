import os
import pathlib
import shutil
import signal
import time
from datetime import datetime, timezone

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


def fetch_file_modified_time(url):
    """
    Fetches the file modified time for the given URL.

    Args:
    url (str): The URL to fetch the file modified time for.

    Returns:
    str: The file modified time for the given URL.
    """
    response = requests.head(url)
    response.raise_for_status()

    date_string = response.headers.get("last-modified")
    date_format = "%a, %d %b %Y %H:%M:%S %Z"
    # parse the date string and convert to UTC timezone
    date_utc = datetime.strptime(date_string, date_format).replace(tzinfo=timezone.utc)
    return date_utc


def fetch_size(url):
    """
    Fetches the size of the file at the given URL.

    Args:
    url (str): The URL to fetch the file size for.

    Returns:
    int: The size of the file at the given URL.
    """
    response = requests.head(url)
    response.raise_for_status()
    return int(response.headers.get("Content-Length", 0))


def check_etag(url, etag):
    if etag == fetch_etag(url):
        return True
    return False


def file_requires_update(url, dest_path, etag):
    print(f"Checking {dest_path}...", flush=True)
    etag_up_to_date = check_etag(url, etag)
    path_exists = dest_path is not None and dest_path.exists()
    if not etag_up_to_date and path_exists:
        modified = datetime.fromtimestamp(dest_path.stat().st_mtime, tz=timezone.utc)
        remote_modified = fetch_file_modified_time(url)
        if modified < remote_modified:
            return True
        else:
            return False
    if etag_up_to_date and path_exists:
        return False
    return True


def download_or_update_file(url, local_filename, info, dest_path=None):
    print(f"Checking {local_filename}...", flush=True)
    etag_up_to_date = check_etag(url, info, f"{local_filename}-etag")
    path_exists = dest_path is not None and dest_path.exists()
    if etag_up_to_date and path_exists:
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

    temp_dest_path = pathlib.Path(f"{dest_path}.part")

    download_path = temp_dest_path or dest_path

    total_size = fetch_size(url)

    headers = {}
    if download_path.exists():
        file_size = os.path.getsize(download_path)
        print(f"Resuming download of {local_filename}", flush=True)
        print(f"File size: {file_size}", flush=True)
        print(f"Total size: {total_size}", flush=True)
        print(f"Range: bytes={file_size}-{total_size}", flush=True)
        headers = {"Range": f"bytes={file_size}-{total_size}"}
        mode = "ab"
    else:
        mode = "wb"

    # Download the file
    with requests.get(url, headers=headers, stream=True) as response:
        response.raise_for_status()
        download_start_time = time.time()
        progress_thread = threads.ProgessTrackThread(
            download_path, download_start_time, total_size
        )
        signal_handler = utils.SignalHandler(progress_thread)
        signal.signal(signal.SIGINT, signal_handler)

        progress_thread.start()
        print(f"Start downloading {local_filename}", flush=True)
        with open(download_path, mode) as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        etag = fetch_etag(url)
        utils.update_key_in_info_file(f"{local_filename}-etag", etag)

        progress_thread.stop()

    if temp_dest_path is not None:
        shutil.move(temp_dest_path, dest_path)


def download_and_prepare_wow_client(install_folder, url):
    wow_client_zip_file = "wow.zip"
    wow_client_zip_path = install_folder / wow_client_zip_file
    download_file(url, wow_client_zip_path)
    utils.prepare_wow_folder(install_folder, wow_client_zip_path)
