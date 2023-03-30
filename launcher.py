import os
import pathlib
import tempfile

from gooey import Gooey, GooeyParser
from mega import Mega

import download
import utils


@Gooey(
    disable_progress_bar_animation=True,
    progress_regex=r"^Progress: (\d+)% (.*)$",
    progress_expr="x[0]",
)
def parse_args():
    parser = GooeyParser(description="My Cool Gooey App!")
    parser.add_argument(
        "--Folder",
        help="Choose your install path",
        widget="DirChooser",
        default=f"{os.getcwd()}/WoW-Duskhaven",
    )
    args = parser.parse_args()
    return args


def main(args):
    tempfile.tempdir = args.Folder
    install_folder = pathlib.Path(args.Folder)
    mega = Mega()
    mega = mega.login()
    install_folder.mkdir(parents=True, exist_ok=True)

    links = {
        "wow-exe": {
            "url": "https://mega.nz/file/tXQDzAxR#"
            "vZjuc9-Z2Hz8I7y9he30WOJzixJFDwfemJmQiEidjsA",
            "original_md5": [
                "eb8cacb30853dc6ee46f8f7510ee8f48",
                "45892bdedd0ad70aed4ccd22d9fb5984",
            ],
        },
        "patch-5": "https://mega.nz/file/2wAVRLpY#"
        "5if76Akjm2ygtMo3M897mLlXgkKNYWqUsucR2o_UwgM",
        "patch-z": "https://mega.nz/file/Cs5VkaDa#"
        "hAk6K_Nw3fq_iPpe2cc6s3g7Izec8MqPajpfLrrOdrU",
        "wow-folder": {
            "url": "https://tenshrock.fr/?smd_process_download=1&download_id=321",
            "md5": "79f9495ddc561729170241dcc5b5e86a",
        },
    }

    print("Checking WoW Installation", flush=True)
    if not utils.check_wow_install(install_folder):
        print("Did not find an installed WoW client", flush=True)
        download.download_and_prepare_wow_client(
            install_folder,
            wow_client_link_info=links["wow-folder"],
            wow_exe_link_info=links["wow-exe"],
        )

    print("Checking wow.exe...", flush=True)
    download.download_mega_file(
        mega, links["wow-exe"]["url"], str(install_folder), "wow.exe"
    )
    print("Checking patch-5.MPQ...", flush=True)
    download.download_mega_file(
        mega, links["patch-5"], str(install_folder / "Data"), "patch-5.MPQ"
    )
    print("Checking patch-z.MPQ...", flush=True)
    download.download_mega_file(
        mega, links["patch-z"], str(install_folder / "Data"), "patch-z.MPQ"
    )


def more_main():
    main(parse_args())


if __name__ == "__main__":
    more_main()
