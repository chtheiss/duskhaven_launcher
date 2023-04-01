# Duskhaven Updater

Simple progam to download or update the WoW 3.3.5a client and the patch-z, patch-5, patch-A and custom wow.exe required to play on the Duskhaven WoW server.

### Current functionality
- Download the WoW 3.3.5a client if it is not already downloaded and unpack it in the approriate folder
- Adjust the realmlist, remove cinematics and remove the original Wow.exe
- Download/Update the custom files (patch-z, patch-5, patch-A and wow.exe) required to play on Duskhaven
- Automatic resume of interrupted downloads

### Build locally
Install the requirements by running:
```
pip install -r requirements.txt
pip install pyinstaller
```

Run the pyinstaller:
```
pyinstaller --windowed -F .\launcher.py
```
