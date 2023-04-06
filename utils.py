import hashlib
import logging
import os
import pathlib
import shutil
import zipfile

import requests

logging.basicConfig(
    filename="launcher.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("Utils")


def calculate_md5(filepath):
    with open(filepath, "rb") as file:
        hash = hashlib.md5()
        while chunk := file.read(8192):
            hash.update(chunk)
    return hash.hexdigest()


def check_wow_install(install_folder):
    files = [
        "common.MPQ",
        "common-2.MPQ",
        "expansion.MPQ",
        "lichking.MPQ",
        "patch.MPQ",
        "patch-2.MPQ",
        "patch-3.MPQ",
    ]

    for file in files:
        data_file = install_folder / "Data" / file
        logger.info(f"Checking: {data_file}")
        if not data_file.exists():
            logger.info(
                f"The data file {data_file} does not exist. "
                "Assuming no WoW client is installed."
            )
            return False
    return True


def prepare_wow_folder(install_folder, wow_client_zip_path):
    successful = True
    # Extract WoW zip
    if wow_client_zip_path.exists():
        logger.info(f"Unzipping {wow_client_zip_path}")
        with zipfile.ZipFile(wow_client_zip_path, "r") as zip_ref:
            zip_ref.extractall(install_folder)

    logger.info("Moving files")
    source_path = install_folder / "WoW 3.3.5/"

    files = source_path.glob("**/*")
    for file in files:
        parts = list(file.parts)
        parts.remove("WoW 3.3.5")
        destination = pathlib.Path(*parts)
        logger.info(f"Moving {file}")
        shutil.move(file, destination)
    logger.info("Files Moved")

    if len(list(source_path.glob("**/*"))) == 0:
        logger.info("Removing old directory")
        try:
            shutil.rmtree(source_path)
        except FileNotFoundError:
            logger.info(f"Folder does not exist: {source_path}")

    original_wow_exe_path = install_folder / "Wow.exe"
    if os.path.exists(original_wow_exe_path):
        logger.info("Removing old Wow.exe")
        os.remove(original_wow_exe_path)

    cinematics = ["wow_fotlk_1024.avi", "wow_wrathgate_1024.avi"]
    cinematics_folder = install_folder / "Data" / "enUS" / "Interface" / "Cinematics"
    for cinematic in cinematics:
        cinematic_path = cinematics_folder / cinematic
        if cinematic_path.exists():
            logger.info(f"Removing cinematics file: {cinematic_path}")
            os.remove(cinematic_path)

    logger.info("Changing realmlist")
    realm_list_path = install_folder / "Data" / "enUS" / "realmlist.wtf"
    with open(realm_list_path, "w") as realm_list_file:
        realm_list_file.write("set realmlist duskhaven.servegame.com")

    # Remove the zip file at the end
    if successful:
        os.remove(wow_client_zip_path)

    return successful


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
