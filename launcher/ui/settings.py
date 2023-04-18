import os
import shutil
import subprocess
import sys
from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QVBoxLayout,
)

from launcher import credentials
from launcher.ui import fonts, helpers
from launcher.ui.button import Button
from launcher.ui.quit_button import QuitButton


class SettingsDialog(QDialog):
    def __init__(self, basedir, main_window):
        super().__init__()
        self.basedir = Path(basedir)
        self.main_window = main_window

        # Set up the UI
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 300)
        self._width, self._height = self.adjust_size()
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.installation_path = Path(
            self.main_window.configuration.get("installation_path", "")
        )

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
            "Deletes all settings and cached data from the launcher "
            "(Including credentials). \n"
            "This will not affect your game installation."
        )
        if (
            self.main_window.configuration.get("install_in_progress", False)
            or self.main_window.configuration.get("installation_path", None) is None
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
        self.limit_bandwidth.setChecked(
            self.main_window.configuration.get("limit_bandwidth", False)
        )
        self.limit_bandwidth.setText("Limit bandwidth to:")
        self.limit_bandwidth.setFont(fonts.NORMAL)
        self.limit_bandwidth.toggled.connect(self.set_limit_bandwidth)

        self.bandwidth = QSpinBox()
        self.bandwidth.setRange(0, 10000000)
        self.bandwidth.setSingleStep(10)
        self.bandwidth.setSuffix(" KB/s")
        self.bandwidth.setValue(self.main_window.configuration.get("bandwidth", 0))
        self.bandwidth.setEnabled(
            self.main_window.configuration.get("limit_bandwidth", False)
        )
        self.bandwidth.valueChanged.connect(self.set_bandwidth)
        bandwidth_layout.addWidget(self.limit_bandwidth)
        bandwidth_layout.addWidget(self.bandwidth)

        self.ignore_updates = QCheckBox()
        self.ignore_updates.setText("Do not check for Game updates")
        self.ignore_updates.setChecked(
            self.main_window.configuration.get("ignore_updates", False)
        )
        self.ignore_updates.setFont(fonts.NORMAL)
        self.ignore_updates.toggled.connect(self.set_ignore_updates)

        self.delete_client_zip = QCheckBox()
        self.delete_client_zip.setText("Delete wow-client.zip after installation")
        self.delete_client_zip.setChecked(
            self.main_window.configuration.get("delete_client_zip_after_install", False)
        )
        self.delete_client_zip.setFont(fonts.NORMAL)
        self.delete_client_zip.toggled.connect(self.set_delete_client_zip)

        layout.addLayout(top_bar_layout)
        layout.addWidget(installation_label)
        layout.addLayout(installation_layout)
        layout.addWidget(helpers.create_divider())
        layout.addWidget(cache_label)
        layout.addLayout(cache_layout)
        layout.addWidget(helpers.create_divider())
        layout.addWidget(download_label)
        layout.addLayout(bandwidth_layout)
        layout.addWidget(self.ignore_updates)
        layout.addWidget(self.delete_client_zip)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.setStyleSheet(
            """
            QDialog {
                background-color: rgba(27, 47, 78, 150);
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
        self.main_window.configuration.save()
        self.accept()

    def set_ignore_updates(self):
        self.main_window.configuration[
            "ignore_updates"
        ] = self.ignore_updates.isChecked()
        self.main_window.configuration.save()

    def set_limit_bandwidth(self):
        self.main_window.configuration[
            "limit_bandwidth"
        ] = self.limit_bandwidth.isChecked()
        if self.limit_bandwidth.isChecked():
            self.bandwidth.setEnabled(True)
        else:
            self.bandwidth.setEnabled(False)
        self.main_window.configuration.save()

    def set_bandwidth(self):
        if self.limit_bandwidth.isChecked():
            self.main_window.configuration["bandwidth"] = self.bandwidth.value()
            self.main_window.configuration.save()

    def delete_launcher_cache(self):
        entities_to_remove = list(self.main_window.configuration)
        self.main_window.login.save_credentials.setChecked(False)
        self.main_window.progress_bar.progress_bar_label.autoplay.autoplay.setChecked(
            False
        )
        self.main_window.login.lineEdit_username.setText("")
        self.main_window.login.lineEdit_password.setText("")

        for key in entities_to_remove:
            if key not in ["installation_path"]:
                self.main_window.configuration.pop(key, None)
        self.main_window.configuration.save()

        credentials.delete_account_name()
        credentials.delete_password()

    def set_delete_client_zip(self):
        self.main_window.configuration[
            "delete_client_zip_after_install"
        ] = self.delete_client_zip.isChecked()
        self.main_window.configuration.save()
