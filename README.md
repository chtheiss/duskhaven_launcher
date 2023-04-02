# Duskhaven Updater

Simple progamm to download or update the WoW 3.3.5a client and the patch-z, patch-5, patch-A and custom wow.exe required to play on the Duskhaven WoW server.

The newest release is available [here](https://github.com/chtheiss/duskhaven_launcher/releases).

<p align="center">
    <img src="https://github.com/chtheiss/duskhaven_launcher/blob/main/readme-images/launcher.png" />
</p>

### Current functionality

- Download the WoW 3.3.5 client if it is not already downloaded and unpack it in the appropriate folder
- Adjust the realmlist, remove cinematics and remove the original Wow.exe
- Download/Update the custom files (patch-z, patch-5, patch-A and wow.exe) required to play on Duskhaven
- Automatic resume of interrupted downloads
- The launcher saves the version info of the different files and the installation folder in a `config.json`. The `launcher.exe` and `config.json` **must be in the same folder**.

### Known Issues

- Download speed and time tracking is a bit wonky when pausing/resuming a download
- The Launcher cannot detect what version the customs files are if you have downloaded them manually. Hence it needs to redownload the custom files even if you have them already. For the WoW client itself with have MD5 hashes so that you do not need to redownload the original client itself
- Styling and positioning of elements is off on many devices (depending on your resolution)
- The launcher currently has no functionality to check if there is a new version of the launcher available

### Build locally

Install the requirements by running:

```
pip install -r requirements.txt
pip install pyinstaller
```

Run the pyinstaller:

```
pyinstaller pylauncher.spec
```
