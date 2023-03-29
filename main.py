import threading
from gooey import Gooey
from mega import Mega
from gooey import GooeyParser
import os
import tempfile
import pathlib

#@Gooey(progress_regex=r"^Progress: (\d+)%$")
def parse_args():
    parser = GooeyParser(description="My Cool Gooey App!")
    parser.add_argument('--Folder', help="Choose your install path", widget='DirChooser', default=os.getcwd()) 
    args = parser.parse_args()
    return args

def background_progress():
    threading.Timer(0.5, background_progress).start()
    tempfiles = pathlib.Path(tempfile.gettempdir()).glob("wow_megapy_*")   
    for temp in tempfiles:
          print(temp)

def main(args):
    mega = Mega()

    m = mega.login()

    links = {
          "wow-exe": 'https://mega.nz/file/tXQDzAxR#vZjuc9-Z2Hz8I7y9he30WOJzixJFDwfemJmQiEidjsA',
          "patch-5": "https://mega.nz/file/2wAVRLpY#5if76Akjm2ygtMo3M897mLlXgkKNYWqUsucR2o_UwgM",
          "patch-z": "https://mega.nz/file/Cs5VkaDa#hAk6K_Nw3fq_iPpe2cc6s3g7Izec8MqPajpfLrrOdrU",
          "wow-folder": "https://download.stormforge.gg/Wow335.zip?__cf_chl_tk=EwChkLjhmCQ39fBWF36siFT8Q4eaS7fxtKuEFf68SCQ-1680114539-0-gaNycGzNDRA",
    }

    import time
    background_progress()

    for i in range(1):
        time.sleep(1)
        print(f"Progress: {(i+1)*10}%")

    m.download_url(links["wow-exe"], dest_path=".", dest_filename="wow.exe",)

def more_main():
	args = parse_args()
	main(parse_args())
	

if __name__ == "__main__":
	more_main()