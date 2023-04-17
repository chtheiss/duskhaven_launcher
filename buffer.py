   # Create layouts

        # Create widgets

        self.create_start_button()
        # Add widgets to layouts
        self.main_layout.addLayout(top_bar_layout)


        dialog_created = self.create_installation_dialog()
        if not dialog_created:
            self.button_layout.setContentsMargins(0, 0, 0, self.height * 0.01)
        else:
            self.button_layout.setContentsMargins(0, 10, 0, self.height * 0.01)


        if self.start_button.text() == "PLAY":
            self.progress_bar.setValue(100 * 100)
            self.progress_bar.setFormat("")
            self.progress_bar_label.setText("100%")

        # Connect signals to slots

        # Set stylesheet
        self.setStyleSheet(
            """

        QPushButton#start {
            color: white;
            background-color: #0078d7;
            margin-right: 10px;
            margin-left: 30px;
            border-radius: 0px;
            border: 0
        }

        QPushButton#start:hover {
            background-color: #0063ad;
        }

        QLabel#installation_path_label {
            color: white;
        }

        QLineEdit#installation_path_text {
            color: white;
            border: none;
            margin-left: 40px;
            margin-right: 40px;
        }

        QPushButton#browse {
            color: white;
            background-color: #0078d7;
            margin-right: 10px;
            margin-left: 30px;
            border-radius: 0px;
            border: 0;
        }

        QPushButton#browse:hover {
            background-color: #0063ad;
        }
        """
        )


    def set_installing_label(self):
        self.progress_bar_label.setText(
            f"Installing Base Game {self.number_install_dots * '.'}"
        )
        if self.number_install_dots == 3:
            self.number_install_dots = 0
        self.number_install_dots += 1


    def update_config(self, key, value):
        self.configuration[key] = value
        self.configuration.save()

    def create_start_button(self):
        if not hasattr(self, "start_button"):
            self.start_button = QPushButton("Start")
            self.start_button.setObjectName("start")
            self.start_button.setMinimumHeight(self.height * 0.07)
            self.start_button.setMinimumWidth(self.width * 0.2)
            self.start_button.setCursor(QCursor(Qt.PointingHandCursor))
            self.start_button.setFont(fonts.NORMAL)

        if self.check_first_time_user():
            logger.info("Setting interaction button to INSTALL")
            self.start_button.setText("INSTALL")
            self.start_button.clicked.connect(self.start_install_game)
        elif self.configuration.get("install_in_progress", False):
            logger.info("Setting interaction button to RESUME INSTALL")
            self.start_button.setText("RESUME INSTALL")
            self.start_button.clicked.connect(self.download_install_game)
        elif self.configuration.get("download_queue"):
            logger.info("Setting interaction button to UPDATE")
            self.start_button.setText("UPDATE")
            self.start_button.clicked.connect(self.update_game)
        else:
            logger.info("Setting interaction button to PLAY")
            self.start_button.setText("PLAY")
            self.start_button.clicked.connect(self.start_game)
            self.set_autoplay()

    def create_installation_dialog(self):
        if self.check_first_time_user():
            self.installation_path_label = QLabel(
                "<p style='color:white;'>Installation Path: </p>"
            )
            self.installation_path_label.setFont(fonts.NORMAL)
            self.installation_path_text = QLineEdit()
            self.installation_path_text.setText(
                self.configuration.get(
                    "installation_path", os.path.join(os.getcwd(), "WoW Duskhaven")
                )
            )
            self.installation_path_text.setFont(fonts.NORMAL)
            self.installation_path_text.setReadOnly(True)

            self.browse_button = QPushButton("Browse")
            self.browse_button.setObjectName("browse")
            self.browse_button.setMinimumHeight(self.height * 0.07)
            self.browse_button.setMinimumWidth(self.width * 0.2)
            self.browse_button.setCursor(QCursor(Qt.PointingHandCursor))
            self.browse_button.setFont(fonts.NORMAL)

            self.installation_path_layout = QHBoxLayout()
            self.installation_path_layout.addWidget(self.installation_path_label)
            self.installation_path_layout.addWidget(self.installation_path_text)
            self.installation_path_layout.addWidget(self.browse_button)
            self.main_layout.addLayout(self.installation_path_layout)
            self.browse_button.clicked.connect(self.show_installation_dialog)
            return True
        return False

    def update_game(self):
        logger.info("Updating game.")
        if not self.task:
            file = self.configuration["download_queue"][0]
            url = Config.LINKS[file]
            self.create_runnable(
                url=url,
                dest_path=pathlib.Path(self.configuration["installation_path"]) / file,
                paused_download_etag=self.configuration.get("paused_download_etag"),
            )
            self.task.start()
            self.start_button.setText("PAUSE")
        elif self.task.paused:
            self.start_button.setText("PAUSE")
            self.task.resume(self.configuration.get("paused_download_etag"))
        else:
            self.start_button.setText("RESUME")
            self.task.pause()

    def create_runnable(self, *args, **kwargs):
        self.task = threads.BackgroundTask(*args, **kwargs, settings=self.configuration)
        self.task.signals.progress_update.connect(self.update_progress)
        self.task.signals.progress_label_update.connect(self.update_progress_label)
        self.task.signals.finished_download.connect(self.download_next_or_stop)
        self.task.signals.finished_launcher_download.connect(
            self.complete_launcher_update
        )
        self.task.signals.failed_download.connect(self.restart_download_task)
        self.task.signals.update_config.connect(self.update_config)

    def restart_download_task(self):
        logger.info("Restarting download task.")
        self.task = None
        self.update_game()

    def update_launcher(self, assets):
        if hasattr(self, "browse_button"):
            self.browse_button.setVisible(False)
            self.installation_path_label.setVisible(False)
            self.installation_path_text.setVisible(False)

        self.start_button.setText("UPDATING LAUNCHER")
        self.start_button.setEnabled(False)
        self.autoplay.setCheckable(False)
        self.autoplay.setChecked(False)
        if hasattr(self, "autoplay_timer"):
            self.autoplay_timer.stop()

        if getattr(sys, "frozen", False):
            executable_path = pathlib.Path(sys.executable)
        else:
            executable_path = pathlib.Path(sys.argv[0])

        possible_assets = [
            asset for asset in assets if asset["name"].endswith(executable_path.suffix)
        ]
        if len(possible_assets) == 0:
            logger.warning("Changed file extension!")
        elif len(possible_assets) > 1:
            logger.warning("Found multiple assets")

        asset = possible_assets[0]

        logger.info(
            f"Start downloading {asset['name']} "
            f"from {asset['browser_download_url']}"
        )

        file = asset["name"] + ".new"
        self.create_runnable(
            url=asset["browser_download_url"], dest_path=file, paused_download_etag=None
        )
        self.task.total_size = asset["size"]
        self.task.start()

    def complete_launcher_update(self, new_version_path):
        if getattr(sys, "frozen", False):
            # The application is frozen.
            executable_path = pathlib.Path(sys.executable)
        else:
            # The application is not frozen.
            # We assume the script is being executed from the command line.
            executable_path = pathlib.Path(sys.argv[0])

        logger.info(f"Name of current launcher: {executable_path}")

        new_version_path = pathlib.Path(new_version_path)

        temp_name = "temp_launcher"
        try:
            executable_path.rename(executable_path.parent / temp_name)
            time.sleep(1)
        except Exception as e:
            logger.error(e)
        try:
            new_version_path.rename(executable_path)
            time.sleep(1)
        except Exception as e:
            logger.error(e)

        self.configuration["just_updated"] = True
        self.configuration.save()

        time.sleep(2)
        logger.info(f"Starting Launcher: {executable_path}")
        try:
            subprocess.Popen(str(executable_path), shell=True).wait()
        except Exception as e:
            logger.error(e)
        QApplication.quit()


    def start_install_game(self):
        logger.info("Start install game")
        if hasattr(self, "browse_button"):
            self.browse_button.setVisible(False)
            self.installation_path_label.setVisible(False)
            self.installation_path_text.setVisible(False)
        # Did not attempt to install yet and user clicked install
        if hasattr(self, "installation_path_text"):
            install_folder = self.installation_path_text.text()
        else:
            install_folder = self.configuration["installation_path"]

        if "installation_path" not in self.configuration:
            self.configuration["installation_path"] = install_folder
            self.configuration.save()

        status = self.check_wow_install()
        if status == "update":
            logger.info("Game installed but requires updates.")
            self.start_button.setText("PAUSE")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.update_game)
            self.download_next_or_stop(None, None)
            return
        if status == "play":
            logger.info("Game already up-to-date.")
            self.start_button.setText("PLAY")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.start_game)
            return

        download_queue = self.configuration.get("download_queue", [])
        wow_zip_dest_path = pathlib.Path(install_folder) / "wow-client.zip"
        if "wow-client.zip" not in download_queue and not wow_zip_dest_path.exists():
            self.configuration["download_queue"] = ["wow-client.zip"] + download_queue
            self.configuration.save()
        utils.add_outdated_files_to_queue(self.configuration)

        if wow_zip_dest_path.exists():
            self.start_install_task(wow_zip_dest_path)
        else:
            self.download_install_game()
            self.start_button.setText("PAUSE")
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.pause_install_game)

    def pause_install_game(self):
        logger.info("Pause install game")
        self.start_button.setText("RESUME")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.resume_install_game)
        self.task.pause()

    def resume_install_game(self):
        logger.info("Resume install game")
        self.start_button.setText("PAUSE")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.pause_install_game)
        self.task.resume(self.configuration.get("paused_download_etag"))

    def download_install_game(self):
        logger.info("Download install game")
        if not self.task:
            self.start_button.setText("PAUSE")
            self.configuration["install_in_progress"] = True
            self.configuration.save()
            pathlib.Path(self.configuration["installation_path"]).mkdir(
                parents=True, exist_ok=True
            )
            if len(self.configuration["download_queue"]) > 0:
                file = self.configuration["download_queue"][0]
                url = Config.LINKS[file]
                self.create_runnable(
                    url=url,
                    dest_path=pathlib.Path(self.configuration["installation_path"])
                    / file,
                    paused_download_etag=self.configuration.get("paused_download_etag"),
                )
                self.task.start()
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.pause_install_game)
            else:
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.start_game)
                self.start_button.setText("PLAY")
                self.set_autoplay()

    def check_first_time_user(self):
        # Check if this is the first time the user has run the launcher
        return not self.configuration.get("installation_path")

    def check_wow_install(self):
        # If WoW already installed -> update or play
        if utils.check_wow_install(
            pathlib.Path(self.configuration["installation_path"])
        ):
            utils.add_outdated_files_to_queue(self.configuration)
            if hasattr(self, "browse_button"):
                self.browse_button.setVisible(False)
                self.installation_path_label.setVisible(False)
                self.installation_path_text.setVisible(False)
            # If any file needs update -> update
            if len(self.configuration["download_queue"]) > 0:
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.update_game)
                self.start_button.setText("UPDATE")
                self.start_button.setEnabled(True)
                return "update"
            # All files up-to-date -> play
            else:
                self.start_button.clicked.disconnect()
                self.start_button.clicked.connect(self.start_game)
                self.start_button.setText("PLAY")
                self.start_button.setEnabled(True)
                return "play"

        self.start_button.setEnabled(True)
        return "install"

    def show_installation_dialog(self):
        # Prompt the user to select the installation path
        selected_directory = QFileDialog.getExistingDirectory(
            self, "Select Game Installation Path"
        )
        if selected_directory:
            self.configuration["installation_path"] = selected_directory
            self.installation_path_text.setText(selected_directory)
            self.configuration.save()
            self.start_button.setEnabled(False)
            self.check_wow_install()

    def finish_base_install(self, install_successful):
        if self.task:
            self.task.quit()
            self.task.wait()
            self.task = None
        if self.install_task:
            self.install_task.quit()
            self.install_task.wait()
            self.install_task = None

        if hasattr(self, "install_label_timer"):
            self.install_label_timer.stop()

        download_queue = self.configuration.get("download_queue", [])
        if len(download_queue) > 0 and download_queue[0] == "wow-client.zip":
            self.configuration["download_queue"] = download_queue
            removed_download = self.configuration["download_queue"].pop(0)
            logger.info(f"Removing {removed_download} from download queue.")
            logger.info(f"Download queue: {self.configuration['download_queue']}")
            self.configuration.save()

        if not install_successful:
            self.progress_bar_label.setText("Installation Failed!")
            return

        self.start_button.setEnabled(True)
        self.start_button.clicked.connect(self.update_game)
        self.update_game()

    def start_install_task(self, dest_path):
        self.number_install_dots = 1
        self.install_label_timer = QTimer()
        self.start_button.setEnabled(False)
        self.start_button.setText("EXCTRACTING CLIENT")
        self.start_button.clicked.disconnect()
        self.install_label_timer.timeout.connect(self.set_installing_label)
        self.install_label_timer.start(1000)
        self.install_task = threads.InstallWoWTask(
            pathlib.Path(self.configuration["installation_path"]),
            pathlib.Path(dest_path),
            self.configuration.get("delete_client_zip_after_install", False),
        )
        self.install_task.signals.install_finished.connect(self.finish_base_install)
        self.install_task.start()

    def download_next_or_stop(
        self, dest_path: Optional[str] = None, etag: Optional[str] = None
    ):
        # Download the next file in the queue or stop the download
        if dest_path and etag:
            file_versions = self.configuration.get("file_versions", {})
            file_versions[pathlib.Path(dest_path).name] = etag
            self.configuration["file_versions"] = file_versions
            self.configuration["paused_download_etag"] = None
            removed_download = self.configuration["download_queue"].pop(0)
            logger.info(
                "download_next_or_stop: Removing "
                f"{removed_download} from download queue."
            )
            logger.info(
                "download_next_or_stop: Download queue: "
                f"{self.configuration['download_queue']}"
            )
            self.configuration.save()

        if self.task:
            self.task.quit()
            self.task.wait()
            self.task = None

        if dest_path is not None and pathlib.Path(dest_path).name == "wow-client.zip":
            self.start_install_task(dest_path)
            return

        download_queue = self.configuration.get("download_queue", [])
        if download_queue:
            file = download_queue[0]
            self.create_runnable(
                url=Config.LINKS[file],
                dest_path=pathlib.Path(self.configuration["installation_path"]) / file,
                paused_download_etag=self.configuration.get("paused_download_etag"),
            )
            self.task.start()
        else:
            self.configuration["install_in_progress"] = False
            self.configuration.save()
            if self.task:
                self.task.quit()
                self.task.wait()
                self.task = None
            self.start_button.clicked.disconnect()
            self.start_button.clicked.connect(self.start_game)
            self.start_button.setText("PLAY")
            self.set_autoplay()

    def update_progress_label(self, info):
        self.progress_bar_label.setText(info)

    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage * 100)
        # displaying the decimal value
        self.progress_bar.setFormat("")
