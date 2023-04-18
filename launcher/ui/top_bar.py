import logging
from functools import partial

from PySide6 import QtCore
from PySide6.QtGui import QCursor, QIcon, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from launcher import ui, version
from launcher.ui import fonts

logging.basicConfig(
    filename="launcher.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("Topbar")


class LinkLabel(QLabel):
    def __init__(self, text, url, parent=None) -> None:
        super().__init__(parent)
        self.url = url
        self.shown_text = text
        self.setText(
            "<a style='color: #7699cf; text-decoration: none; font-weight: bold;' "
            f"href='{url}'>{self.shown_text}</a>"
        )
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setOpenExternalLinks(True)
        self.setFont(fonts.NORMAL)
        self.setContentsMargins(0, 0, 0, 0)

        style = """
            QLabel {
                padding-left: 5px;
                padding-right: 5px;
            }

            QLabel:hover {
                background-color: #7699cf;
            }
        """

        self.setStyleSheet(style)

    def enterEvent(self, event):
        self.setText(
            "<a style='color: white; text-decoration: none; font-weight: bold; "
            "box-shadow: none;' "
            f"href='{self.url}'>{self.shown_text}</a>"
        )

    def leaveEvent(self, event):
        self.setText(
            "<a style='color: #7699cf; text-decoration: none; font-weight: bold;' "
            f"href='{self.url}'>{self.shown_text}</a>"
        )


class MenuButton(QPushButton):
    def __init__(self, icon_path, callback=None, parent=None) -> None:
        super().__init__(parent)

        self.setAutoFillBackground(False)
        self.setText("")
        self.setIcon(QIcon(str(icon_path)))
        self.setIconSize(QtCore.QSize(parent.height() * 0.7, parent.height() * 0.7))
        self.setFlat(True)

        style = """
            QPushButton {
                background-color: rgba(0, 0, 0, 0);
                background-color: transparent;
                border: none;
            }
            QPushButton:focus {
                background-color: rgba(0, 0, 0, 0);
                background-color: transparent;
                border: none;
            }
            QPushButton::icon {
                margin-right: 0px;
                color: white;
            }
        """

        self.setStyleSheet(style)

        if callback is not None:
            self.setCursor(Qt.PointingHandCursor)
            self.clicked.connect(callback)


class TopBar(QWidget):
    def __init__(self, basedir, parent=None) -> None:
        super().__init__(parent)
        self.basedir = basedir

        layout = QHBoxLayout()

        self.register_site_link = LinkLabel("REGISTER", "https://duskhaven.net/", self)
        self.discord_site_link = LinkLabel(
            "DISCORD", "https://discord.gg/duskhaven", self
        )
        self.source_code_link = LinkLabel(
            f"Version {version.version}",
            "https://github.com/chtheiss/duskhaven_launcher",
            self,
        )
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.settings_button = MenuButton(
            icon_path=basedir / "images" / "icons8-settings-64.png",
            callback=partial(self.open_settings_dialog),
            parent=self,
        )

        self.minimize_button = MenuButton(
            icon_path=basedir / "images" / "icons8-minus-64.png",
            callback=partial(self.minimize_launcher),
            parent=self,
        )

        self.quit_button = MenuButton(
            icon_path=basedir / "images" / "icons8-close-button-64.png",
            callback=partial(self.quit_launcher),
            parent=self,
        )

        layout.addWidget(self.register_site_link)
        layout.addWidget(self.discord_site_link)
        layout.addItem(spacer)
        layout.addWidget(self.source_code_link)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.quit_button)

        self.setLayout(layout)

    def minimize_launcher(self):
        logger.info("Minimizing launcher")
        self.window().showMinimized()

    def open_settings_dialog(self):
        # Create the settings dialog and show it
        settings_dialog = ui.SettingsDialog(self.basedir, self.window())
        settings_dialog.exec()

    def quit_launcher(self):
        logger.info("Quitting launcher")
        # Save configuration and quit the application
        self.window().configuration.save()
        if self.window().task:
            logger.info("Closing remaining tasks.")
            self.window().task.quit()
            self.window().task.wait()
            self.window().task = None

        # if hasattr(self.window().server_status_bar, "timer"):
        #    self.window().server_status_bar.timer.stop()

        QApplication.quit()
