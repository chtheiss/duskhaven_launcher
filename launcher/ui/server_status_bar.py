import datetime

import pytz
from PySide6 import QtCore
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QWidget

from launcher import threads
from launcher.ui import helpers


def calculate_daily_reset_time():
    # Set the target timezone to UTC-7
    target_tz = pytz.timezone("America/Los_Angeles")

    local_tz = datetime.datetime.now(pytz.timezone("UTC")).astimezone().tzinfo

    # Get the current local time
    now_local = datetime.datetime.now(local_tz)

    # Convert to UTC
    now_utc = now_local.astimezone(pytz.utc)

    # Set the time to 5:00 am in UTC-7
    target_time = datetime.time(5, 0)
    target_dt = datetime.datetime.combine(now_utc.date(), target_time)
    # Convert to the target timezone
    target_dt_tz = target_tz.localize(target_dt)
    if target_dt_tz < now_utc:
        target_dt_tz += datetime.timedelta(days=1)
    # Convert back to the local timezone
    target_dt_local = target_dt_tz.astimezone(local_tz)

    next_weekday = target_dt_local.weekday()
    next_weekday_name = datetime.date(1900, 1, next_weekday + 1).strftime("%a")

    # Calculate the time difference
    time_diff = target_dt_local - now_local

    # Get the total number of minutes until the target datetime
    total_minutes = int(time_diff.total_seconds() / 60)

    # Calculate the number of hours and minutes
    hours = total_minutes // 60
    minutes = total_minutes % 60

    # Return the results as a tuple
    return (next_weekday_name, target_dt_local.strftime("%H:%M"), hours, minutes)


def calculate_weekly_reset_time():
    # Set the target timezone to UTC-7
    target_tz = pytz.timezone("America/Los_Angeles")

    local_tz = datetime.datetime.now(pytz.timezone("UTC")).astimezone().tzinfo

    # Get the current local time
    now_local = datetime.datetime.now(local_tz)

    # Convert to UTC
    now_utc = now_local.astimezone(pytz.utc)

    # Set the time to 5:00 am in UTC-7 on Tuesday
    target_time = datetime.time(5, 0)
    target_dt = datetime.datetime.combine(now_utc.date(), target_time)

    days_until_reset_day = (
        1 - now_utc.weekday()
    ) % 7  # calculate days until next Tuesday
    target_dt_tz = target_tz.localize(target_dt)

    if days_until_reset_day == 0 and now_local > target_dt_tz:
        days_until_reset_day = 7
    # next_monday_date = today + datetime.timedelta(days=days_until_next_monday)
    target_dt_tz += datetime.timedelta(days=days_until_reset_day)

    # Convert to the target timezone

    # Convert back to the local timezone
    target_dt_local = target_dt_tz.astimezone(local_tz)

    next_reset_day = target_dt_local.weekday()
    next_reset_day_name = datetime.date(1900, 1, next_reset_day + 1).strftime("%a")

    # Calculate the time difference
    time_diff = target_dt_local - now_local

    # Get the total number of minutes until the target datetime
    total_minutes = int(time_diff.total_seconds() / 60)

    # Calculate the number of days, hours, and minutes
    days = total_minutes // (60 * 24)
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60

    # Return the results as a tuple
    return (
        next_reset_day_name,
        target_dt_local.strftime("%H:%M"),
        days,
        hours,
        minutes,
    )


class ServerStatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        server_layout = QGridLayout()

        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(27, 47, 78, 220))
        self.setPalette(p)

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
                color: yellow;
                font-size: 16px;
                margin-bottom: 2px;
                font-weight: bold;
            }
        """

        game_server_label = QLabel("Game Server:")
        game_server_label.setStyleSheet(server_label_style)

        login_server_label = QLabel("Login Server:")
        login_server_label.setStyleSheet(server_label_style)

        self.game_server_status_label = QLabel("CHECKING")
        self.game_server_status_label.setStyleSheet(status_label_style)

        self.login_server_status_label = QLabel("CHECKING")
        self.login_server_status_label.setStyleSheet(status_label_style)

        daily_reset_label = QLabel()
        daily_reset_label.setStyleSheet(server_label_style)

        daily_reset_timer_label = QLabel()
        daily_reset_timer_label.setStyleSheet(server_label_style)

        weekly_reset_label = QLabel()
        weekly_reset_label.setStyleSheet(server_label_style)

        weekly_reset_timer_label = QLabel()
        weekly_reset_timer_label.setStyleSheet(server_label_style)

        (
            next_weekday_name,
            target_dt_local,
            hours,
            minutes,
        ) = calculate_daily_reset_time()
        daily_reset_label.setText(f"Daily Reset: {next_weekday_name} {target_dt_local}")
        daily_reset_timer_label.setText(f"{hours:02d}h {minutes:02d}m until reset")

        (
            next_reset_day_name,
            target_dt_local,
            days,
            hours,
            minutes,
        ) = calculate_weekly_reset_time()
        weekly_reset_label.setText(
            f"Weekly Reset: {next_reset_day_name} {target_dt_local}"
        )
        weekly_reset_timer_label.setText(
            f"{days:02d}d {hours:02d}h {minutes:02d}m until reset"
        )

        server_layout.addWidget(game_server_label, 0, 0)
        server_layout.addWidget(self.game_server_status_label, 0, 1)
        server_layout.addWidget(login_server_label, 1, 0)
        server_layout.addWidget(self.login_server_status_label, 1, 1)
        server_layout.addWidget(helpers.create_divider(), 2, 0, 1, 2)
        server_layout.addWidget(daily_reset_label, 3, 0, 1, 2)
        server_layout.addWidget(daily_reset_timer_label, 4, 0, 1, 2)
        server_layout.addWidget(weekly_reset_label, 5, 0, 1, 2)
        server_layout.addWidget(weekly_reset_timer_label, 6, 0, 1, 2)

        daily_reset_label.setAlignment(Qt.AlignCenter)
        daily_reset_timer_label.setAlignment(Qt.AlignCenter)
        weekly_reset_label.setAlignment(Qt.AlignCenter)
        weekly_reset_timer_label.setAlignment(Qt.AlignCenter)

        server_layout.setAlignment(Qt.AlignCenter)

        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(2)

        self.timer = QTimer()
        self.timer.timeout.connect(self.request_server_status)
        self.timer.start(15000)  # 5000 milliseconds = 5 seconds
        self.request_server_status()
        self.setLayout(server_layout)
        self.setMaximumWidth(parent.width * 0.25)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.adjustSize()

    def paintEvent(self, event):
        # Draw border using QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable anti-aliasing
        painter.setPen(QPen(QColor("#D9D9D9"), 2))
        painter.drawRoundedRect(self.rect(), 5, 5)

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
