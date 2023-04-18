import logging

from PySide6 import QtCore
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from launcher import threads
from launcher.ui import fonts, helpers

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
            self.layout.addWidget(helpers.create_divider())

    def set_news(self, news):
        self.news = news
        self.create_news()


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
        # self.setStyleSheet("QScrollArea { background-color: rgba(34, 59, 98, 220); }")
        self.setStyleSheet("QScrollArea { background-color: rgba(27, 47, 78, 220); }")

    def set_news(self, news):
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
        self.setMinimumSize(0, height)
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
                background-color: rgb(34, 59, 98);
                color: white;
                padding: 8px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #d0d0d0;
            }

            QTabBar::tab:selected {
                background-color: #365d9a;
                color: white;
                border-bottom-color: #365d9a;
            }

            QTabBar::tab:!selected:hover {
                background-color: #4675be;
                border: 1px solid #4675be;
            }

            QTabBar::tab:selected:hover {
                background-color: #4675be;
                border: 1px solid #4675be;
            }
            """
        )

    def request_news(self):
        news_task = threads.NewsTask("news")
        news_task.signals.news.connect(self.set_news)

        changelog_task = threads.NewsTask("changelog")
        changelog_task.signals.changelog.connect(self.set_changelog)

        launcher_news_task = threads.NewsTask("launcher-news")
        launcher_news_task.signals.launcher_news.connect(self.set_launcher_news)

        self.threadpool.start(news_task)
        self.threadpool.start(changelog_task)
        self.threadpool.start(launcher_news_task)

    def set_news(self, news):
        if len(news) == 0:
            news_task = threads.NewsTask("news")
            news_task.signals.news.connect(self.set_news)
            return self.threadpool.start(news_task)
        news = [{"timestamp": n[0], "content": n[1]} for n in news]
        self.news_area.set_news(news)

    def set_changelog(self, news):
        if len(news) == 0:
            changelog_task = threads.NewsTask("changelog")
            changelog_task.signals.changelog.connect(self.set_changelog)
            return self.threadpool.start(changelog_task)
        news = [{"timestamp": n[0], "content": n[1]} for n in news]
        logger.info("Setting changelog")
        self.changelog_area.set_news(news)

    def set_launcher_news(self, news):
        if len(news) == 0:
            launcher_news_task = threads.NewsTask("launcher-news")
            launcher_news_task.signals.launcher_news.connect(self.set_launcher_news)
            return self.threadpool.start(launcher_news_task)
        news = [{"timestamp": n[0], "content": n[1]} for n in news]

        self.launcher_area.set_news(news)
