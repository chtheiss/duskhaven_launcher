import random
import sys

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

import launcher.news as news

# from layout_colorwidget import Color


class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(
            QRect(0, 0, self.width(), self.height()),
            QColor(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            ),
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        pagelayout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self.stacklayout = QStackedLayout()

        pagelayout.addLayout(button_layout)
        pagelayout.addLayout(self.stacklayout)

        btn = QPushButton("red")
        btn.pressed.connect(self.activate_tab_1)
        button_layout.addWidget(btn)
        self.news_layout = QVBoxLayout()
        self.news_labels = [QLabel() for _ in range(21)]
        self.news_widget = QWidget()
        self.news_widget.setLayout(self.news_layout)
        for label in self.news_labels:
            self.news_layout.addWidget(label)

        self.stacklayout.addWidget(self.news_widget)
        self.create_news_timer()

        btn = QPushButton("green")
        btn.pressed.connect(self.activate_tab_2)
        button_layout.addWidget(btn)
        self.stacklayout.addWidget(Overlay())

        btn = QPushButton("yellow")
        btn.pressed.connect(self.activate_tab_3)
        button_layout.addWidget(btn)
        self.stacklayout.addWidget(Overlay())

        widget = QWidget()
        widget.setLayout(pagelayout)
        self.setCentralWidget(widget)

    def activate_tab_1(self):
        self.stacklayout.setCurrentIndex(0)

    def activate_tab_2(self):
        self.stacklayout.setCurrentIndex(1)

    def activate_tab_3(self):
        self.stacklayout.setCurrentIndex(2)

    def create_news_timer(self):
        self.news_timer = QTimer()
        self.news_timer.timeout.connect(
            self.fetch_news
        )  # connect the timer to the update_countdown_label method
        self.news_timer.start(
            60000
        )  # start the timer to fire every 60000ms (60 second)
        self.fetch_news()

    def fetch_news(self):
        latest_news = news.fetch_news()
        for i, n in enumerate(latest_news):
            self.news_labels[i].setText(f"{n['timestamp']}:\n{n['content']}")


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec_()
