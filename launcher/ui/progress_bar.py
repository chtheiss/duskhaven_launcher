from PySide6.QtCore import QTimer
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from launcher.ui import fonts


class Autoplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()

        self.autoplay_in_label = QLabel("")
        self.autoplay_in_label.setObjectName("autoplay_in_label")
        self.autoplay_in_label.setFont(fonts.SMALL)
        self.autoplay_in_label.setStyleSheet(
            """
            color: white;
            margin-right: 5px;
            """
        )

        self.autoplay = QCheckBox()
        self.autoplay.setText("AUTO-PLAY")
        self.autoplay.setFont(fonts.SMALL)
        self.autoplay.setLayoutDirection(Qt.RightToLeft)
        self.autoplay.setChecked(self.window().configuration.get("autoplay", False))
        self.autoplay.toggled.connect(self.set_autoplay)

        layout.addWidget(self.autoplay_in_label)
        layout.addWidget(self.autoplay)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    def set_autoplay(self):
        if self.autoplay.isChecked():
            self.window().configuration["autoplay"] = True
            self.window().configuration.save()
            if self.window().configuration.get("start_button_state", "") == "PLAY":
                self.remaining_seconds = 5  # set the initial value of remaining seconds
                self.autoplay_timer = QTimer()
                self.autoplay_timer.timeout.connect(
                    self.update_countdown_label
                )  # connect the timer to the update_countdown_label method
                self.autoplay_in_label.setText(f"{self.remaining_seconds} seconds")
                self.autoplay_timer.start(
                    1000
                )  # start the timer to fire every 1000ms (1 second)
        else:
            self.window().configuration["autoplay"] = False
            if hasattr(self, "autoplay_timer"):
                self.autoplay_timer.stop()
                self.autoplay_in_label.setText("")
            self.window().configuration.save()

    def update_countdown_label(self):
        self.remaining_seconds -= 1  # decrement the remaining seconds
        self.autoplay_in_label.setText(
            f"{self.remaining_seconds} seconds"
        )  # update the label text
        if self.remaining_seconds == 0:
            self.autoplay_timer.stop()  # stop the timer when the countdown is over
            self.autoplay_in_label.setText("")
            self.window().start_game()


class ProgessBarLabel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()

        self.progress_bar_label = QLabel("")
        self.progress_bar_label.setMinimumHeight(self.window().height * 0.05)
        self.progress_bar_label.setFont(fonts.SMALL)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.autoplay = Autoplay(self)

        layout.addWidget(self.progress_bar_label)
        layout.addItem(spacer)
        layout.addWidget(self.autoplay)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet(
            """
                QLabel {
                    color: white!important;
                    margin-top: 0px;
                    margin-left: 40px;

                }

                QCheckBox {
                    color: white!important;
                    margin-right: 5px;
                }
            """
        )

        self.setLayout(layout)

    def update_progress_label(self, info):
        self.progress_bar_label.setText(info)


class ProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        self.progress_bar_label = ProgessBarLabel(self)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress")
        self.progress_bar.setRange(0, 10000)
        self.progress_bar.setMaximumHeight(self.parent().height * 0.02)

        if self.window().configuration.get("start_button_state", "") == "PLAY":
            self.progress_bar.setValue(100 * 100)
            self.progress_bar.setFormat("")
            self.progress_bar_label.update_progress_label("100%")

        layout.addWidget(self.progress_bar_label)
        layout.addWidget(self.progress_bar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet(
            """
                QProgressBar {
                    background-color: #444444;
                }

                QProgressBar::chunk {
                    background-color: #0078d7!important;
                }
            """
        )

        self.setLayout(layout)

    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage * 100)
        # displaying the decimal value
        self.progress_bar.setFormat("")
