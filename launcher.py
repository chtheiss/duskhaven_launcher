import os
import pathlib
import tempfile

from gooey import Gooey, GooeyParser

import download
import utils
from config import Config


@Gooey(
    disable_progress_bar_animation=False,
    # progress_regex=r"^Progress: (\d+)% (.*)$",
    # progress_expr="x[0]",
)
def parse_args():
    parser = GooeyParser(description="My Cool Gooey App!")
    info = utils.load_or_create_info_file()

    default_folder = info.get("install_folder", f"{os.getcwd()}/WoW-Duskhaven")

    parser.add_argument(
        "--Folder",
        help="Choose your install path",
        widget="DirChooser",
        default=default_folder,
    )
    args = parser.parse_args()

    if "install_folder" not in info:
        info = utils.update_key_in_info_file("install_folder", args.Folder)
    else:
        if info["install_folder"] != args.Folder:
            info = utils.update_key_in_info_file("install_folder", args.Folder)

    return args


def main(args):
    info = utils.load_or_create_info_file()

    tempfile.tempdir = info["install_folder"]

    install_folder = pathlib.Path(info["install_folder"])
    install_folder.mkdir(parents=True, exist_ok=True)

    """
    print("Checking WoW Installation", flush=True)
    if utils.check_wow_install(install_folder):
        print("Found existing WoW client", flush=True)
    else:
        print("Did not find an installed WoW client", flush=True)
        download.download_and_prepare_wow_client(
            install_folder,
            wow_client_link_info=Config.LINKS["wow-folder"],
            wow_exe_link_info=Config.LINKS["wow-exe"],
        )
    """

    dest_paths = [
        install_folder / "wow.exe",
        install_folder / "Data" / "patch-5.MPQ",
        install_folder / "Data" / "patch-A.MPQ",
        install_folder / "Data" / "patch-Z.mpq",
    ]
    for dest_path in dest_paths:
        file = str(dest_path.name)
        download.download_or_update_file(Config.LINKS[file], file, info, dest_path)


def more_main():
    main(parse_args())


if __name__ == "__main__":
    more_main()
