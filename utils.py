import hashlib
import json
import os
import pathlib
import shutil
import sys
import zipfile

import requests


class SignalHandler:
    def __init__(self, thread):
        self.thread = thread

    def __call__(self, sig, frame):
        print("Interrupt signal received. Stopping background threads...", flush=True)
        self.thread.stop()
        sys.exit()


def calculate_md5(filepath):
    with open(filepath, "rb") as file:
        hash = hashlib.md5()
        while chunk := file.read(8192):
            hash.update(chunk)
    return hash.hexdigest()


def load_or_create_info_file():
    info_file = pathlib.Path("wow_updater_info.json")
    if info_file.exists():
        with info_file.open("r") as file:
            return json.load(file)
    else:
        with info_file.open("w") as file:
            json.dump({}, file)
            return {}


def update_key_in_info_file(key, value):
    info_file = pathlib.Path("wow_updater_info.json")
    info = load_or_create_info_file()
    info[key] = value
    with info_file.open("w") as file:
        json.dump(info, file)
    return info


def check_wow_install(install_folder):
    data_hashes = {
        "common.MPQ": "b6e12d3c24f734b81ad6f029017b1f6f",
        "common-2.MPQ": "5722cdeed794fd1008191d7541136fce",
        "expansion.MPQ": "f64dc65c049f29a9fb3653e36a0b356c",
        "lichking.MPQ": "1c53d82557d0b3632a23622a38a0f8d2",
        "patch.MPQ": "6e099a82d9d2bb75c037625aecaa34aa",
        "patch-2.MPQ": "06f5f1ca2f427fba59c216521fcdda54",
        "patch-3.MPQ": "35733b76fcf0f95a0d8240d1f36cc5c3",
    }
    for file, hash in data_hashes.items():
        data_file = install_folder / "Data" / file
        print(f"Checking: {data_file}", flush=True)
        if not data_file.exists():
            print(
                f"The data file {data_file} does not exist. "
                "Assuming no WoW client is installed.",
                flush=True,
            )
            return False
        md5_match = calculate_md5(data_file) == hash
        if not md5_match:
            print(
                "It seems you have a wrong version of WoW installed. "
                f"Your {data_file} does not match.",
                flush=True,
            )
            return False
    return True


def prepare_wow_folder(install_folder, wow_client_zip_path):
    successful = True
    # Extract WoW zip
    if wow_client_zip_path.exists():
        print(f"Unzipping {wow_client_zip_path}", flush=True)
        with zipfile.ZipFile(wow_client_zip_path, "r") as zip_ref:
            zip_ref.extractall(install_folder)

    print("Moving files", flush=True)
    source_path = install_folder / "WoW 3.3.5/"

    files = source_path.glob("**/*")
    for file in files:
        parts = list(file.parts)
        parts.remove("WoW 3.3.5")
        destination = pathlib.Path(*parts)
        print(f"Moving {file}")
        shutil.move(file, destination)
    print("Files Moved", flush=True)

    if len(list(source_path.glob("**/*"))) == 0:
        print("Removing old directory", flush=True)
        try:
            shutil.rmtree(source_path)
        except FileNotFoundError:
            print(f"Folder does not exist: {source_path}", flush=True)

    original_wow_exe_path = install_folder / "Wow.exe"
    if os.path.exists(original_wow_exe_path):
        print("Removing old Wow.exe", flush=True)
        os.remove(original_wow_exe_path)

    cinematics = ["wow_fotlk_1024.avi", "wow_wrathgate_1024.avi"]
    cinematics_folder = install_folder / "Data" / "enUS" / "Interface" / "Cinematics"
    for cinematic in cinematics:
        cinematic_path = cinematics_folder / cinematic
        if cinematic_path.exists():
            print(f"Removing cinematics file: {cinematic_path}", flush=True)
            os.remove(cinematic_path)

    print("Changing realmlist", flush=True)
    realm_list_path = install_folder / "Data" / "enUS" / "realmlist.wtf"
    with open(realm_list_path, "w") as realm_list_file:
        realm_list_file.write("set realmlist duskhaven.servegame.com")

    # Remove the zip file at the end
    if successful:
        os.remove(wow_client_zip_path)


def compare_versions(v1, v2):
    v1 = v1.removeprefix("v")
    v2 = v2.removeprefix("v")
    # Split the version strings into major, minor, and patch components
    v1_parts = v1.split(".")
    v2_parts = v2.split(".")

    # Compare major version
    if int(v1_parts[0]) > int(v2_parts[0]):
        return 1
    elif int(v1_parts[0]) < int(v2_parts[0]):
        return -1

    # Compare minor version
    if int(v1_parts[1]) > int(v2_parts[1]):
        return 1
    elif int(v1_parts[1]) < int(v2_parts[1]):
        return -1

    # Compare patch version
    if int(v1_parts[2]) > int(v2_parts[2]):
        return 1
    elif int(v1_parts[2]) < int(v2_parts[2]):
        return -1

    # Versions are equal
    return 0


def get_latest_release():
    # Construct the URL for the GitHub API request
    url = "https://api.github.com/repos/chtheiss/duskhaven_launcher/releases/latest"

    # Make the API request and parse the response as JSON
    response = requests.get(url)
    data = response.json()

    # Extract the tag name and asset names
    tag_name = data["tag_name"]
    assets = [asset for asset in data["assets"]]

    # Return the results as a tuple
    return (tag_name, assets)
