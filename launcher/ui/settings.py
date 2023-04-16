import os
import shutil
import subprocess
import sys
from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
)

from launcher import credentials
from launcher.ui import fonts
from launcher.ui.button import Button
from launcher.ui.quit_button import QuitButton


class SettingsDialog(QDialog):
    def __init__(self, main_window, settings, basedir):
        super().__init__()
        self.settings = settings
        self.basedir = Path(basedir)
        self.main_window = main_window

        # Set up the UI
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 300)
        self._width, self._height = self.adjust_size()
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.installation_path = Path(self.settings.get("installation_path", ""))

        layout = QVBoxLayout()

        section_label_style = """
            QLabel {
                font-weight: bold;
                margin-bottom: 10px;
                color: white;
            }
        """

        top_bar_layout = QHBoxLayout()
        top_bar_layout.setAlignment(Qt.AlignRight)

        self.quit_button = QuitButton(
            os.path.join(basedir, "images", "icons8-close-button-64.png"),
            self._width * 0.02,
            self.close,
        )
        top_bar_layout.addWidget(self.quit_button)

        installation_label = QLabel("Client Folders")
        installation_label.setStyleSheet(section_label_style)
        installation_label.setFont(fonts.LARGE)

        installation_layout = QHBoxLayout()
        installation_layout.setAlignment(Qt.AlignLeft)

        installation_path_button = Button(
            self,
            "Installation Folder",
            partial(self.open_path, self.installation_path),
        )
        if not self.installation_path.exists():
            installation_path_button.setEnabled(False)

        addon_path = self.installation_path / "Interface" / "AddOns"
        addon_path_button = Button(
            self,
            "Addon Folder",
            partial(
                self.open_path,
                addon_path,
            ),
        )
        if not addon_path.exists():
            addon_path_button.setEnabled(False)
            addon_path_button.setToolTip("Addon folder does not exist.")

        installation_layout.addWidget(installation_path_button)
        installation_layout.addWidget(addon_path_button)

        # Create a horizontal divider line

        cache_label = QLabel("Cache")
        cache_label.setStyleSheet(section_label_style)
        cache_label.setFont(fonts.LARGE)

        cache_layout = QHBoxLayout()
        cache_layout.setAlignment(Qt.AlignLeft)
        installation_layout.setContentsMargins

        cache_path = self.installation_path / "Cache"
        clear_cache_button = Button(
            self,
            "Clear Game Cache",
            self.delete_cache,
        )
        clear_cache_button.setToolTip(
            "Deletes the Cache folder. \nThis will not affect your game installation."
        )
        if not cache_path.exists():
            clear_cache_button.setEnabled(False)
            clear_cache_button.setToolTip("Cache folder does not exist.")

        clear_launcher_cache_button = Button(
            self,
            "Clear Launcher Cache",
            self.delete_launcher_cache,
        )
        clear_launcher_cache_button.setToolTip(
            "Deletes all configuration files and cached data from the launcher "
            "(Including credentials). \n"
            "This will not affect your game installation."
        )
        if (
            self.settings.get("install_in_progress", False)
            or self.settings.get("installation_path", None) is None
        ):
            clear_launcher_cache_button.setEnabled(False)
            clear_launcher_cache_button.setToolTip(
                "Cannot clear launcher cache while an installation is in progress."
            )

        cache_layout.addWidget(clear_cache_button)
        cache_layout.addWidget(clear_launcher_cache_button)

        download_label = QLabel("Download")
        download_label.setStyleSheet(section_label_style)
        download_label.setFont(fonts.LARGE)

        bandwidth_layout = QHBoxLayout()
        bandwidth_layout.setAlignment(Qt.AlignLeft)
        self.limit_bandwidth = QCheckBox()
        self.limit_bandwidth.setChecked(self.settings.get("limit_bandwidth", False))
        self.limit_bandwidth.setText("Limit bandwidth to:")
        self.limit_bandwidth.setFont(fonts.NORMAL)
        self.limit_bandwidth.toggled.connect(self.set_limit_bandwidth)

        self.bandwidth = QSpinBox()
        self.bandwidth.setRange(0, 10000000)
        self.bandwidth.setSingleStep(10)
        self.bandwidth.setSuffix(" KB/s")
        self.bandwidth.setValue(self.settings.get("bandwidth", 0))
        self.bandwidth.setEnabled(self.settings.get("limit_bandwidth", False))
        self.bandwidth.valueChanged.connect(self.set_bandwidth)
        bandwidth_layout.addWidget(self.limit_bandwidth)
        bandwidth_layout.addWidget(self.bandwidth)

        self.ignore_updates = QCheckBox()
        self.ignore_updates.setText("Do not check for Game updates")
        self.ignore_updates.setChecked(self.settings.get("ignore_updates", False))
        self.ignore_updates.setFont(fonts.NORMAL)
        self.ignore_updates.toggled.connect(self.set_ignore_updates)

        self.delete_client_zip = QCheckBox()
        self.delete_client_zip.setText("Delete wow-client.zip after installation")
        self.delete_client_zip.setChecked(
            self.settings.get("delete_client_zip_after_install", False)
        )
        self.delete_client_zip.setFont(fonts.NORMAL)
        self.delete_client_zip.toggled.connect(self.set_delete_client_zip)

        layout.addLayout(top_bar_layout)
        layout.addWidget(installation_label)
        layout.addLayout(installation_layout)
        layout.addWidget(self.create_divider())
        layout.addWidget(cache_label)
        layout.addLayout(cache_layout)
        layout.addWidget(self.create_divider())
        layout.addWidget(download_label)
        layout.addLayout(bandwidth_layout)
        layout.addWidget(self.ignore_updates)
        layout.addWidget(self.delete_client_zip)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.setStyleSheet(
            """
            QDialog {
                background-color: #00001D;
                color: white;
            }

            QCheckBox {
                color: white;
            }
            QSpinBox {
                background-color: #f5f5f5;
                border: 1px solid #d8d8d8;
                padding: 5px;
                padding-right: 15px;
                border-radius: 5px;
                color: #00001D;
            }
            QSpinBox:disabled {
                background-color: #d8d8d8;
            }

            """
        )

        self.setLayout(layout)

    def create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        palette = line.palette()
        palette.setColor(QPalette.WindowText, Qt.white)
        line.setPalette(palette)
        line.setFixedHeight(1)
        line.setStyleSheet(
            """
            QFrame {
                margin: 0px;
            }
            """
        )
        return line

    def delete_cache(self):
        shutil.rmtree(self.installation_path / "Cache")

    def open_path(self, path):
        # Open the path in the OS's file manager
        if sys.platform.startswith("win"):
            subprocess.call(["explorer", path])
        elif sys.platform.startswith("linux"):
            subprocess.call(["xdg-open", path])

    def adjust_size(self):
        # Set the size and position of the launcher based on the
        # size and resolution of the screen
        screen = self.screen()
        screen_geometry = screen.geometry()

        width = screen_geometry.width() * 0.4
        height = screen_geometry.height() * 0.4
        x = (screen_geometry.width() - width) / 2
        y = (screen_geometry.height() - height) / 2
        self.setGeometry(x, y, width, height)
        return width, height

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
            # set cursor to move shape
            self.setCursor(QCursor(Qt.SizeAllCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = None
            event.accept()
            # reset cursor to default
            self.setCursor(Qt.ArrowCursor)

    def close(self):
        self.settings.save()
        self.accept()

    def set_ignore_updates(self):
        self.settings["ignore_updates"] = self.ignore_updates.isChecked()
        self.settings.save()

    def set_limit_bandwidth(self):
        self.settings["limit_bandwidth"] = self.limit_bandwidth.isChecked()
        if self.limit_bandwidth.isChecked():
            self.bandwidth.setEnabled(True)
        else:
            self.bandwidth.setEnabled(False)
        self.settings.save()

    def set_bandwidth(self):
        if self.limit_bandwidth.isChecked():
            self.settings["bandwidth"] = self.bandwidth.value()
            self.settings.save()

    def delete_launcher_cache(self):
        log_path = self.basedir / "launcher.log"
        if log_path.exists():
            log_path.unlink()
        entities_to_remove = list(self.settings)
        for key in entities_to_remove:
            if key not in ["installation_path"]:
                self.settings.pop(key, None)
        self.settings.save()

        self.main_window.login.lineEdit_username.setText("")
        self.main_window.login.lineEdit_password.setText("")
        credentials.delete_account_name()
        credentials.delete_password()

    def set_delete_client_zip(self):
        self.settings[
            "delete_client_zip_after_install"
        ] = self.delete_client_zip.isChecked()
        self.settings.save()
