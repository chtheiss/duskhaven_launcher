import os

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QWidget

from launcher import ui
from launcher.ui import fonts


class InstallationDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()

        self.installation_path_label = QLabel(
            "<p style='color:white;'>Installation Path: </p>"
        )
        self.installation_path_label.setFont(fonts.NORMAL)

        self.installation_path_text = QLineEdit()
        self.installation_path_text.setText(
            self.window().configuration.get(
                "installation_path", os.path.join(os.getcwd(), "WoW Duskhaven")
            )
        )
        self.installation_path_text.setFont(fonts.NORMAL)
        self.installation_path_text.setReadOnly(True)

        self.browse_button = ui.Button(self, "Browse", self.show_installation_dialog)

        layout.addWidget(self.installation_path_label)
        layout.addWidget(self.installation_path_text)
        layout.addWidget(self.browse_button)

        self.setLayout(layout)

    def show_installation_dialog(self):
        # Prompt the user to select the installation path
        selected_directory = QFileDialog.getExistingDirectory(
            self, "Select Game Installation Path"
        )
        if selected_directory:
            self.window().configuration["installation_path"] = selected_directory
            self.installation_path_text.setText(selected_directory)
            self.window().configuration.save()
            self.window().check_wow_install()
