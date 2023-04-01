import hashlib
import json
import os
import pathlib
import shutil
import zipfile


class SignalHandler:
    def __init__(self, thread):
        self.thread = thread

    def __call__(self, sig, frame):
        print("Interrupt signal received. Stopping background threads...", flush=True)
        self.thread.stop()


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


def prepare_wow_folder(install_folder, wow_client_zip_path, wow_exe_md5_hashes):
    successful = True
    # Extract WoW zip
    if wow_client_zip_path.exists():
        print(f"Unzipping {wow_client_zip_path}", flush=True)
        with zipfile.ZipFile(wow_client_zip_path, "r") as zip_ref:
            zip_ref.extractall(install_folder)

    print("Moving files", flush=True)
    source_path = install_folder / "World of Warcraft 3.3.5a.12340 enGB/"

    files = source_path.glob("**/*")
    for file in files:
        parts = list(file.parts)
        parts.remove("World of Warcraft 3.3.5a.12340 enGB")
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
    if (
        os.path.exists(original_wow_exe_path)
        and calculate_md5(original_wow_exe_path) in wow_exe_md5_hashes
    ):
        print("Removing old Wow.exe", flush=True)
        os.remove(original_wow_exe_path)

    cinematics = ["wow_fotlk_1024.avi", "wow_wrathgate_1024.avi"]
    cinematics_folder = install_folder / "Data" / "enGB" / "Interface" / "Cinematics"
    for cinematic in cinematics:
        cinematic_path = cinematics_folder / cinematic
        if cinematic_path.exists():
            print(f"Removing cinematics file: {cinematic_path}", flush=True)
            os.remove(cinematic_path)

    print("Changing realmlist", flush=True)
    realm_list_path = install_folder / "Data" / "enGB" / "realmlist.wtf"
    with open(realm_list_path, "w") as realm_list_file:
        realm_list_file.write("set realmlist duskhaven.servegame.com")

    # Remove the zip file at the end
    if successful:
        os.remove(wow_client_zip_path)
