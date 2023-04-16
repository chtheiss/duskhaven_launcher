from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from launcher import credentials


class Login(QWidget):
    def __init__(self, app_config, max_width):
        super().__init__()
        self.app_config = app_config
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
        layout.addWidget(label_name, 1, 0)
        layout.addWidget(self.lineEdit_username, 2, 0)

        label_password = QLabel("<p> PASSWORD </p>")
        label_password.setStyleSheet(label_name_style)
        self.lineEdit_password = QLineEdit()
        self.lineEdit_password.setStyleSheet(line_edit_style)
        password_ = credentials.get_password()
        if password_ is not None:
            self.lineEdit_password.setText(password_)
        self.lineEdit_password.textChanged.connect(self.password_editing_finished)
        self.lineEdit_password.setEchoMode(QLineEdit.Password)

        layout.addWidget(label_password, 3, 0)
        layout.addWidget(self.lineEdit_password, 4, 0)

        self.setLayout(layout)

    def username_changed(self):
        credentials.set_account_name(self.lineEdit_username.text())

    def password_editing_finished(self):
        credentials.set_password(self.lineEdit_password.text())
