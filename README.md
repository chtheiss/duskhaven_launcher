# Duskhaven Updater

**This project is not associated with the Duskhaven Team in any way and is independently developed!**

Simple progamm to download or update the WoW 3.3.5a client and the patch-z, patch-5, patch-A and custom wow.exe required to play on the Duskhaven WoW server.

## **The newest release is available [here](https://github.com/chtheiss/duskhaven_launcher/releases/latest/)**

<p align="center">
    <img src="https://github.com/chtheiss/duskhaven_launcher/blob/main/readme-images/launcher.png" />
</p>

### Current functionality

- Download the WoW 3.3.5 client if it is not already downloaded and unpack it in the appropriate folder
- Adjust the realmlist, remove cinematics and remove the original Wow.exe
- Adds config.wtf on clean install to have a more pleasant first launch of the game
- Download/Update the custom files (patch-z, patch-5, patch-A and wow.exe) required to play on Duskhaven
- **Pause/Resume** of interrupted downloads
- Securely save account name and password to automatically login after starting the wow client
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
  - Specify if the client zip file should be deleted after a successful installation (default behavior is **not** removing it)
- Checkbox to automatically delete WDB before starting the game
- If possible:
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
python -m nuitka --standalone --enable-plugin=pyside6 --disable-console --onefile --include-data-dir=images=images --windows-icon-from-ico=images/favicon.ico --output-dir=dist  --include-module="win32timezone"  duskhaven_launcher.py
```

Linux:

```
conda install libpython-static
python -m nuitka --standalone --enable-plugin=pyside6 --disable-console --onefile --include-data-dir=images=images --output-dir=dist  duskhaven_launcher.py
```

# Wine Prefix Setup

## **For Linux and Mac OSX**

## Instructions modified for Duskhaven from [Ascension.gg](https://ascension.gg/download/unix)

## by @jimmon89

### **Step 1 - Installing Dependencies**

Debian/Ubuntu:
In order for the game to function you are required to install WINE and WINEtricks on your system.

```
sudo apt update -qq
sudo apt install -qqy wine winetricks mono-complete
```

Manjaro/Arch

```
sudo pacman -Syu
sudo pacman -S wine winetricks mono
```

CentOS

```
sudo yum update -q
sudo yum install -qy wine winetricks mono-complete
```

### **Step 2 - Setting up Duskhaven WINE bottle**

Open a Terminal and enter the following
(NOTE: this will be a part of the launch script to run Duskhaven)

```
export WINEPREFIX="/home/$USER/.local/share/Duskhaven/prefix/"
export WINEARCH=win32
```

### **Step 3 - Installing dependencies for WINE**

Finish up the mandatory steps of the manual installation by installing the remaining dependencies below:

```
mkdir -p "/home/$USER/.local/share/Duskhaven/prefix/"
winetricks win10 ie8 corefonts dotnet48 vcrun2019 dxvk
```

### **Step 4 - Install this launcher**

```
cd "/home/$USER/.local/share/Duskhaven/"
wget https://github.com/chtheiss/duskhaven_launcher/releases/latest/download/duskhaven_launcher.bin
chmod +x ./duskhaven_launcher.bin
```

### **Step 5 - Create script to run Duskhaven**

The personal recommendation for ease of use is to create a simple shell script to tie all of this together

```
touch ./run_duskhaven.sh
chmod +x ./run_duskhaven.sh
echo '#!'$(which sh) > ./run_duskhaven.sh
echo cd \"/home/$USER/.local/share/Duskhaven/\" >> ./run_duskhaven.sh
echo export WINEPREFIX=\"/home/$USER/.local/share/Duskhaven/prefix/\" >> ./run_duskhaven.sh
echo export WINEARCH=win32 >> ./run_duskhaven.sh
echo ./duskhaven_launcher.bin >> ./run_duskhaven.sh
```

### **BONUS: Create Application shortcut to launch script**

```
cd "/home/$USER/.local/share/applications/"
touch ./Duskhaven.desktop
chmod +x ./Duskhaven.desktop
echo \[Desktop Entry\] > ./Duskhaven.desktop
echo Type=Application >> ./Duskhaven.desktop
echo Categories=Game >> ./Duskhaven.desktop
echo Name=Duskhaven >> ./Duskhaven.desktop
echo Exec=/home/$USER/.local/share/Duskhaven/run_duskhaven.sh >> ./Duskhaven.desktop
echo Path=/home/$USER/.local/share/Duskhaven/ >> ./Duskhaven.desktop
```
