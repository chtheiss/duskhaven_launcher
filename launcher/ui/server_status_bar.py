from PySide6 import QtCore
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from launcher import threads


class ServerStatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        server_layout = QGridLayout()
        server_label_style = """
            QLabel {
                color: white;
                font-size: 16px;
                margin-bottom: 2px;
                font-weight: bold;
            }
        """

        status_label_style = """
            QLabel {
                color: green;
                font-size: 16px;
                margin-bottom: 2px;
                font-weight: bold;
            }
        """

        game_server_label = QLabel("Game Server:")
        game_server_label.setStyleSheet(server_label_style)

        login_server_label = QLabel("Login Server:")
        login_server_label.setStyleSheet(server_label_style)

        self.game_server_status_label = QLabel()
        self.game_server_status_label.setStyleSheet(status_label_style)

        self.login_server_status_label = QLabel()
        self.login_server_status_label.setStyleSheet(status_label_style)

        server_layout.addWidget(game_server_label, 0, 0)
        server_layout.addWidget(self.game_server_status_label, 0, 1)
        server_layout.addWidget(login_server_label, 1, 0)
        server_layout.addWidget(self.login_server_status_label, 1, 1)

        layout.addLayout(server_layout)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(2)

        self.timer = QTimer()
        self.timer.timeout.connect(self.request_server_status)
        self.timer.start(15000)  # 5000 milliseconds = 5 seconds
        self.request_server_status()

        self.setLayout(layout)

    def request_server_status(self):
        if not self.window().isMinimized():
            self.game_task = threads.ServerStatusTask("game")
            self.game_task.signals.game_server_status.connect(
                self.set_game_server_status
            )

            self.login_task = threads.ServerStatusTask("login")
            self.login_task.signals.login_server_status.connect(
                self.set_login_server_status
            )
            self.threadpool.start(self.game_task)
            self.threadpool.start(self.login_task)

    def set_game_server_status(self, alive):
        style = """
                font-size: 16px;
                margin-bottom: 2px;
                font-weight: bold;
        """
        if alive:
            current_style = style + "color: green;"
            self.game_server_status_label.setText("ONLINE")
            self.game_server_status_label.setStyleSheet(current_style)
        else:
            current_style = style + "color: red;"
            self.game_server_status_label.setText("OFFLINE")
            self.game_server_status_label.setStyleSheet(current_style)

    def set_login_server_status(self, alive):
        style = """
                font-size: 16px;
                margin-bottom: 2px;
                font-weight: bold;
        """
        if alive:
            current_style = style + "color: green;"
            self.login_server_status_label.setText("ONLINE")
            self.login_server_status_label.setStyleSheet(current_style)
        else:
            current_style = style + "color: red;"
            self.login_server_status_label.setText("OFFLINE")
            self.login_server_status_label.setStyleSheet(current_style)
