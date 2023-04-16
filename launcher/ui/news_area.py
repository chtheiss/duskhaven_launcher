import logging

from PySide6 import QtCore
from PySide6.QtGui import QPalette, Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from launcher import threads
from launcher.ui import fonts

logging.basicConfig(
    filename="launcher.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("News Tabs")


class NewsWidget(QWidget):
    def __init__(self, parent=None, news=None):
        super().__init__(parent)

        self.news = news or []
        self.news_time_labels = []
        self.news_labels = []
        self.layout = QVBoxLayout()

        self.setLayout(self.layout)

    def create_news(self):
        for news in self.news:
            news_time = QLabel(news["timestamp"])
            news_time.setFont(fonts.NORMAL)
            news_time.setStyleSheet("font-weight: bold;")

            news = QLabel(news["content"])
            news.setWordWrap(True)

            self.layout.addWidget(news_time)
            self.layout.addWidget(news)
            self.layout.addWidget(self.create_divider())

    def set_news(self, news):
        self.news = news
        logger.info("News widget creating news")
        self.create_news()

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


class NewsArea(QScrollArea):
    def __init__(self, parent=None, news=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.news = news

        scroll_bar_style = """
            QScrollBar:vertical {
                border: none;
                background-color: rgba(0, 0, 0, 0);
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(128, 128, 128, 255);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.verticalScrollBar().setStyleSheet(scroll_bar_style)
        self.news_widget = NewsWidget(self, news)
        self.news_widget.setObjectName("news")
        self.news_widget.setStyleSheet(
            """
            QWidget#news {
                background-color: transparent;
            }
            QLabel {
                color: white;
                background-color: transparent;
                padding: 5px
            }"""
        )
        self.setWidget(self.news_widget)
        self.setStyleSheet("QScrollArea { background-color: rgba(0, 0, 29, 220); }")

    def set_news(self, news):
        logger.info("News area setting news")
        self.news = news
        self.news_widget.set_news(news)


class NewsTab(QTabWidget):
    def __init__(self, parent=None, width=100, height=100):
        super().__init__(parent)
        self.news_area = NewsArea()
        self.news_area.setMaximumWidth(width)

        self.changelog_area = NewsArea()
        self.changelog_area.setMaximumWidth(width)

        self.launcher_area = NewsArea()
        self.launcher_area.setMaximumWidth(width)

        self.tabBar().setCursor(Qt.PointingHandCursor)
        self.setMaximumWidth(width)
        self.setMaximumHeight(height)
        self.addTab(self.news_area, "LATEST NEWS")
        self.addTab(self.changelog_area, "CHANGELOG")
        self.addTab(self.launcher_area, "LAUNCHER NEWS")

        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(3)
        self.request_news()

        self.setStyleSheet(
            """
            QTabWidget::tab-bar {
                border: none;
                alignment: left;
            }

            QTabWidget::pane {
                background: transparent;
                border:0;
            }

            QTabBar::tab {
                background: transparent;
            }

            QTabBar::tab {
                background-color: #00285B;
                color: white;
                padding: 8px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #d0d0d0;
            }

            QTabBar::tab:selected {
                background-color: #005099;
                color: white;
                border-bottom-color: #005099;
            }

            QTabBar::tab:!selected:hover {
                background-color: #0064B8;
                border: 1px solid #b9b9b9;
            }

            QTabBar::tab:selected:hover {
                background-color: #0078d7;
                border: 1px solid #0078d7;
            }
            """
        )

    def request_news(self):
        self.news_task = threads.NewsTask("news")
        self.news_task.signals.news.connect(self.set_news)

        self.changelog_task = threads.NewsTask("changelog")
        self.changelog_task.signals.changelog.connect(self.set_changelog)

        self.launcher_news_task = threads.NewsTask("launcher-news")
        self.launcher_news_task.signals.launcher_news.connect(self.set_launcher_news)

        self.threadpool.start(self.news_task)
        self.threadpool.start(self.changelog_task)
        self.threadpool.start(self.launcher_news_task)

    def set_news(self, news):
        news = [{"timestamp": n[0], "content": n[1]} for n in news]
        logger.info("Setting news")
        self.news_area.set_news(news)

    def set_changelog(self, news):
        news = [{"timestamp": n[0], "content": n[1]} for n in news]
        logger.info("Setting changelog")
        self.changelog_area.set_news(news)

    def set_launcher_news(self, news):
        news = [{"timestamp": n[0], "content": n[1]} for n in news]
        logger.info("Setting launcher news")
        self.launcher_area.set_news(news)
