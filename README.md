# Duskhaven Updater

**This project is not associated with the Duskhaven Team in any way and is independently developed!**

Simple progamm to download or update the WoW 3.3.5a client and the patch-z, patch-5, patch-A and custom wow.exe required to play on the Duskhaven WoW server.

The newest release is available [here](https://github.com/chtheiss/duskhaven_launcher/releases).

<p align="center">
    <img src="https://github.com/chtheiss/duskhaven_launcher/blob/main/readme-images/launcher.png" />
</p>

### Current functionality

- Download the WoW 3.3.5 client if it is not already downloaded and unpack it in the appropriate folder
- Adjust the realmlist, remove cinematics and remove the original Wow.exe
- Download/Update the custom files (patch-z, patch-5, patch-A and wow.exe) required to play on Duskhaven
- **Pause/Resume** of interrupted downloads
- Persistent Auto-play checkbox that starts the game automatically if no updates are required
- Experimental support for **Mac/Linux**
- Important links
- Minimize and move
- Tracking for download speed, file size, elapsed time, and time until download finished
- The launcher can live outside the WoW folder (as long as it stays together with the config file)

### Roadmap

- Settings Tab to
  - Change installation folder 📂 of the Client
  - Clear Client Cache
  - Clear Launcher Cache
  - Open game directory
  - Specify if the client zip file should be deleted after a successful installation (default behavior is removing it)
- Checkbox to automatically delete WDB before starting the game
- If possible:
  - Securely save password and automatically login after starting the wow client
  - Add optional download for HD files

### Build locally

Install the requirements by running:

```
pip install -r requirements.txt
pip install nuitka
```

Run the Nuitka:

Windows:

```
python -m nuitka --standalone --enable-plugin=pyside6 --disable-console --onefile --include-data-dir=images=images --windows-icon-from-ico=images/favicon.ico --output-dir=dist --output-file=launcher.exe  duskhaven_launcher.py
```

Linux:

```
conda install libpython-static
python -m nuitka --standalone --enable-plugin=pyside6 --disable-console --onefile --include-data-dir=images=images --output-dir=dist --output-file=launcher.bin  duskhaven_launcher.py
```
