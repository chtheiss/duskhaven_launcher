from PySide6.QtGui import QCursor, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from launcher import credentials
from launcher.ui import fonts


class PasswordQuestionLabel(QLabel):
    def enterEvent(self, event):
        self.setText(
            "<a style='color: white; text-decoration: none; font-weight: bold; "
            "box-shadow: none;' "
            "href='https://duskhaven.net/'>Forgot your password?</a>"
        )

    def leaveEvent(self, event):
        self.setText(
            "<a style='color: #7699cf; text-decoration: none; font-weight: bold;' "
            "href='https://duskhaven.net/'>Forgot your password?</a>"
        )


class Login(QWidget):
    def __init__(self, max_width, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(max_width)
        layout = QGridLayout()

        label_name_style = """
            QLabel {
                color: white;
                font-size: 14px;
                margin-bottom: 2px;
                font-weight: bold;
            }
        """

        line_edit_style = """
            QLineEdit {
                background-color: #F2F2F2;
                border-radius: 5px;
                font-size: 14px;
                padding: 2px;
                border: 2px solid #D9D9D9;
                selection-background-color: #0078D7;
                color: #333333;
            }

            QLineEdit:focus {
                border: 2px solid #0078D7;
                outline: none;
            }

            QLineEdit:disabled {
                background-color: #E6E6E6;
                color: #999999;
            }

            QLineEdit::placeholder {
                color: #999999;
            }
        """

        label_name = QLabel("<p> ACCOUNT NAME </p>")
        label_name.setStyleSheet(label_name_style)
        self.lineEdit_username = QLineEdit()
        self.lineEdit_username.setStyleSheet(line_edit_style)
        account_name = credentials.get_account_name()
        if account_name is not None:
            self.lineEdit_username.setText(account_name)
        self.lineEdit_username.textChanged.connect(self.username_changed)
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 0, 0
        )
        layout.addWidget(label_name, 0, 0, 1, 2)
        layout.addWidget(self.lineEdit_username, 1, 0, 1, 2)

        label_password = QLabel("<p> PASSWORD </p>")
        label_password.setStyleSheet(label_name_style)
        self.lineEdit_password = QLineEdit()
        self.lineEdit_password.setStyleSheet(line_edit_style)
        password_ = credentials.get_password()
        if password_ is not None:
            self.lineEdit_password.setText(password_)
        self.lineEdit_password.textChanged.connect(self.password_editing_finished)
        self.lineEdit_password.setEchoMode(QLineEdit.Password)

        layout.addWidget(label_password, 2, 0, 1, 2)
        layout.addWidget(self.lineEdit_password, 3, 0, 1, 2)

        if not self.window().configuration.get("save_credentials", False):
            self.lineEdit_username.setDisabled(True)
            self.lineEdit_password.setDisabled(True)

        self.forgot_password_label = PasswordQuestionLabel()
        self.forgot_password_label.setText(
            "<a style='color: #7699cf; text-decoration: none; font-weight: bold;' "
            "href='https://duskhaven.net/'>Forgot your password?</a>"
        )
        self.forgot_password_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.forgot_password_label.setOpenExternalLinks(True)
        self.forgot_password_label.setFont(fonts.SMALL)

        self.save_credentials = QCheckBox()
        self.save_credentials.setText("Remember Credentials")
        self.save_credentials.setFont(fonts.SMALL)
        self.save_credentials.setLayoutDirection(Qt.RightToLeft)
        self.save_credentials.setChecked(
            self.window().configuration.get("save_credentials", False)
        )
        self.save_credentials.toggled.connect(self.set_save_credentials)
        self.save_credentials.setStyleSheet("color: white;")

        layout.addWidget(self.save_credentials, 4, 1, 1, 1)
        layout.addWidget(self.forgot_password_label, 4, 0, 1, 1)

        self.setLayout(layout)

    def username_changed(self):
        credentials.set_account_name(self.lineEdit_username.text())

    def password_editing_finished(self):
        credentials.set_password(self.lineEdit_password.text())

    def set_save_credentials(self):
        if self.save_credentials.isChecked():
            self.window().configuration["save_credentials"] = True
            self.window().configuration.save()
            self.lineEdit_username.setEnabled(True)
            self.lineEdit_password.setEnabled(True)
        else:
            self.window().configuration["save_credentials"] = False
            self.window().configuration.save()
            self.lineEdit_username.setText("")
            self.lineEdit_password.setText("")
            credentials.delete_password()
            credentials.delete_account_name()
            self.lineEdit_username.setEnabled(False)
            self.lineEdit_password.setEnabled(False)
