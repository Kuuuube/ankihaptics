import asyncio
import threading
import time
import traceback

import aqt
from aqt.qt import (
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    Qt,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from buttplug import Client, ProtocolSpec, WebsocketConnector

from . import config_util, hooks, logger, util


class AnkiHaptics:
    def __init__(self, mw: aqt.main.AnkiQt) -> None:
        if mw:
            config = config_util.get_config(mw)

            self.menuAction = QAction("Anki Haptics Settings", mw, triggered = lambda: self._setup_settings_window(config))
            mw.form.menuTools.addSeparator()
            mw.form.menuTools.addAction(self.menuAction)

            self.client = None
            self.keep_websocket_thread_alive = True
            self.websocket_command_queue = []
            self.websocket_status = "NOT_STARTED"
            self.websocket_thread = None
            self.currently_scanning = False
            self._start_websocket_thread(config)

    def _start_websocket_thread(self, config: dict) -> None:
        if not self.websocket_thread or (self.websocket_thread and not self.websocket_thread.is_alive()):
            self.keep_websocket_thread_alive = True
            websocket_thread = threading.Thread(target = lambda: util.start_async(lambda: self._start_websocket(config)))
            #Daemon threads are not awaited for shutdown. This prevents Anki from hanging forever due to infinitely running thread.
            websocket_thread.daemon = True
            websocket_thread.start()
            self.websocket_thread = websocket_thread
        else:
            logger.log("Anki Haptics Websocket Starter: Declining websocket start request. Websocket already running.")

    def _cleanup_thread(self) -> None:
        self.keep_websocket_thread_alive = False

    async def _start_websocket(self, config: dict) -> None:
        self.client = Client("Anki Haptics Client", ProtocolSpec.v3)
        self.websocket_status = "STARTING"
        connector = WebsocketConnector(config["websocket_path"], logger = self.client.logger)

        try:
            await self.client.connect(connector)
            self.websocket_status = "OK"
        except Exception as e:  # noqa: BLE001
            self.websocket_status = "ERROR\n" + str(e)
            logger.error_log("Could not connect to server, exiting", traceback.format_exc())
            return

        logger.log("Devices: " + str(self.client.devices))

        hooks.register_hooks(aqt.mw, self)

        while self.keep_websocket_thread_alive:
            while len(self.websocket_command_queue) > 0:
                websocket_command = self.websocket_command_queue.pop(0)
                if websocket_command["command"] == "start_scanning" and not self.currently_scanning:
                    await self.client.start_scanning()
                    self.currently_scanning = True
                elif websocket_command["command"] == "stop_scanning" and self.currently_scanning:
                    await self.client.stop_scanning()
                    self.currently_scanning = False
                elif websocket_command["command"] == "scalar_cmd":
                    try:
                        for device in websocket_command["args"]["devices"]:
                            for actuator in device["actuators"]:
                                await actuator["actuator"].command(device["strength"] * actuator["strength_multiplier"])
                        await asyncio.sleep(websocket_command["args"]["duration"])
                        for device in websocket_command["args"]["devices"]:
                            for actuator in device["actuators"]:
                                await actuator["actuator"].command(0.0)
                    except Exception:  # If anything throws while sending device commands, emergency stop all devices, disconnect, clear queue, and end thread  # noqa: BLE001
                        await self.client.stop_all()
                        await self.client.disconnect()
                        self.websocket_command_queue = []
                        logger.error_log("Websocket hit error while issuing device commands. Emergency stopping all devices and clearing queue.", traceback.format_exc())
                        print("Websocket hit error while issuing device commands. Emergency stopping all devices and clearing queue.")  # noqa: T201
                        print(traceback.format_exc())  # noqa: T201
                        self.websocket_status = "EMERGENCY STOP"
                        return

            await asyncio.sleep(config["websocket_polling_delay_ms"] / 1000)

        await self.client.stop_all()
        await self.client.disconnect()
        self.websocket_status = "DISCONNECTED"

    def _setup_settings_window(self, config: dict) -> None:
        if self.client:
            config = config_util.ensure_device_settings(config, self.client.devices)
        settings_window = QDialog(aqt.mw)
        vertical_layout = QVBoxLayout()

        def trigger_websocket_reconnect() -> None:
            while self.websocket_thread and self.websocket_thread.is_alive():
                self._cleanup_thread()
                #block main thread to give time for other thread to die before spawning another
                one_second = 1000
                if config["websocket_polling_delay_ms"] <= one_second:
                    time.sleep(one_second * 2)
                else:
                    time.sleep(config["websocket_polling_delay_ms"] / one_second * 2)
            self.keep_websocket_thread_alive = True
            self._start_websocket_thread(config)
            time.sleep(config["reconnect_delay"]) #block main thread to give time for other thread to connect before resetting the window
            settings_window.close()
            self._setup_settings_window(config)

        def trigger_refresh() -> None:
            settings_window.close()
            self._setup_settings_window(config)

        def trigger_device_scanning() -> None:
            if not self.currently_scanning:
                scan_button.setText("Stop Scanning for Devices")
                self.websocket_command_queue.append({"command": "start_scanning"})
            else:
                scan_button.setText("Scan for Devices")
                self.websocket_command_queue.append({"command": "stop_scanning"})

        if self.websocket_status != "OK" or not self.client:
            vertical_layout.addWidget(QLabel("Failed to connect to websocket. Status code: " + self.websocket_status))
            reconnect_button = QPushButton("Reconnect", clicked = trigger_websocket_reconnect)
            vertical_layout.addWidget(reconnect_button)
            settings_window.setLayout(vertical_layout)
            settings_window.resize(500, 400)
            if settings_window.exec():
                settings_window.show()
            return

        scan_button_text = "Scan for Devices" if not self.currently_scanning else "Stop Scanning for Devices"

        if len(self.client.devices) <= 0:
            vertical_layout.addWidget(QLabel("No devices found. Websocket status code: " + self.websocket_status))
            scan_button = QPushButton(scan_button_text, clicked = trigger_device_scanning)
            vertical_layout.addWidget(scan_button)
            reconnect_button = QPushButton("Reconnect", clicked = trigger_websocket_reconnect)
            vertical_layout.addWidget(reconnect_button)
            refresh_button = QPushButton("Refresh", clicked = trigger_refresh)
            vertical_layout.addWidget(refresh_button)
            settings_window.setLayout(vertical_layout)
            settings_window.resize(500, 400)
            if settings_window.exec():
                settings_window.show()
            return

        #Top buttons
        top_buttons_horizontal_layout = QHBoxLayout()
        vertical_layout.addLayout(top_buttons_horizontal_layout)
        scan_button = QPushButton(scan_button_text, clicked = trigger_device_scanning)
        top_buttons_horizontal_layout.addWidget(scan_button)
        refresh_button = QPushButton("Refresh", clicked = trigger_refresh)
        top_buttons_horizontal_layout.addWidget(refresh_button)

        #Above Tabs
        devices_horizontal_layout = QHBoxLayout()
        devices_combobox = QComboBox()
        device_names = [*(x.name for x in self.client.devices.values())]
        devices_combobox.addItems(device_names)
        devices_combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        devices_horizontal_layout.addWidget(QLabel("Device: "))
        devices_combobox.setCurrentText(device_names[0])
        def get_device_index(input_config: dict, device_name: str) -> int:
            for i, config_device in enumerate(input_config["devices"]):
                if config_device["device_name"] == device_name:
                    return i
            return 0
        def update_vertical_layout_tabs(device_name: str) -> None:
            current_tab = tabs_frame.currentIndex()
            tab_count = tabs_frame.count()
            for tab_index in reversed(range(tab_count)):
                tabs_frame.widget(tab_index).deleteLater()
            new_config = config_util.ensure_device_settings(config_util.get_config(aqt.mw), self.client.devices)
            self._setup_vertical_layout_tabs(new_config, tabs_frame, get_device_index(new_config, device_name))
            tabs_frame.setCurrentIndex(current_tab)
        devices_combobox.currentTextChanged.connect(update_vertical_layout_tabs)

        devices_horizontal_layout.addWidget(devices_combobox)
        vertical_layout.addLayout(devices_horizontal_layout)

        tabs_frame = QTabWidget()
        vertical_layout.addWidget(tabs_frame)

        self._setup_vertical_layout_tabs(config, tabs_frame, get_device_index(config, device_names[0]))

        #Bottom Buttons
        def _set_config_attributes(config: dict, device_index: int) -> dict:
            config["devices"][device_index] = {
                "device_name": config["devices"][device_index]["device_name"],
                "enabled": tabs_frame.findChild(QCheckBox, "ankihaptics_device_enabled").isChecked(),
                "actuators": config["devices"][device_index]["actuators"],
                "enabled_pattern": tabs_frame.findChild(QLineEdit, "ankihaptics_device_enabled_pattern").text(),
                "again": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_again_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_again_strength").value() / 99, 2),
                },
                "hard": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_hard_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_hard_strength").value() / 99, 2),
                },
                "good": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_good_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_good_strength").value() / 99, 2),
                },
                "easy": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_easy_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_easy_strength").value() / 99, 2),
                },
                "show_question": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_show_question_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_show_question_strength").value() / 99, 2),
                },
                "show_answer": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_show_answer_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_show_answer_strength").value() / 99, 2),
                },
            }
            i = 0
            while i < len(config["devices"][device_index]["actuators"]):
                current_config_actuator = config["devices"][device_index]["actuators"][i]
                config["devices"][device_index]["actuators"][i] = {
                    "index": current_config_actuator["index"],
                    "name": current_config_actuator["name"],
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_actuator_" + str(current_config_actuator["index"])).isChecked(),
                    "strength_multiplier": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_actuator_" + str(current_config_actuator["index"]) + "_strength_multiplier").text(), 0.0),
                }
                i += 1
            config["duration"] = {
                "again": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_again_duration").text(), 0.0),
                "hard": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_hard_duration").text(), 0.0),
                "good": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_good_duration").text(), 0.0),
                "easy": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_easy_duration").text(), 0.0),
                "show_question": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_show_question_duration").text(), 0.0),
                "show_answer": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_show_answer_duration").text(), 0.0),
            }
            config["streak"] = {
                "streak_type": tabs_frame.findChild(QComboBox, "ankihaptics_streak_type").currentText(),
                "again": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_streak_again_box").isChecked(),
                    "strength": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_again_strength").text(), 0.0),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_again_duration").text(), 0.0),
                },
                "hard": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_streak_hard_box").isChecked(),
                    "strength": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_hard_strength").text(), 0.0),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_hard_duration").text(), 0.0),
                },
                "good": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_streak_good_box").isChecked(),
                    "strength": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_good_strength").text(), 0.0),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_good_duration").text(), 0.0),
                },
                "easy": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_streak_easy_box").isChecked(),
                    "strength": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_easy_strength").text(), 0.0),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_easy_duration").text(), 0.0),
                },
                "min_length": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_min").text(), 0.0),
                "max_length": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_max").text(), 0.0),
                "streak_time_epoch_ms": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_streak_time").text(), 0.0) * 60000,
            }
            config_util.set_config(aqt.mw, config)
            return config

        bottom_buttons_horizontal_layout = QHBoxLayout()
        vertical_layout.addLayout(bottom_buttons_horizontal_layout)
        save_button = QPushButton("Save", clicked = lambda _: _set_config_attributes(config, get_device_index(config, devices_combobox.currentText())))
        bottom_buttons_horizontal_layout.addWidget(save_button)
        close_button = QPushButton("Close", clicked = settings_window.reject)
        bottom_buttons_horizontal_layout.addWidget(close_button)

        settings_window.setLayout(vertical_layout)
        settings_window.resize(500, 400)
        if settings_window.exec():
            settings_window.show()


    def _setup_vertical_layout_tabs(self, config: dict, tabs_frame: QTabWidget, device_index: int) -> None:
        #General Tab
        general_tab = QWidget()
        general_tab_scroll_area = QScrollArea()
        general_tab_scroll_area.setWidgetResizable(True)
        general_tab_vertical_layout = QVBoxLayout()
        general_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        general_tab.setLayout(general_tab_vertical_layout)
        general_tab_scroll_area.setWidget(general_tab)
        tabs_frame.addTab(general_tab_scroll_area, "General")

        device_enabled = QCheckBox("Device Enabled")
        device_enabled.setObjectName("ankihaptics_device_enabled")
        device_enabled.setChecked(config["devices"][device_index]["enabled"])
        general_tab_vertical_layout.addWidget(device_enabled)

        device_enabled_pattern_box = QHBoxLayout()
        device_enabled_pattern_box.addWidget(QLabel("Enabled Pattern"))
        device_enabled_pattern = QLineEdit()
        device_enabled_pattern.setText(str(config["devices"][device_index]["enabled_pattern"]))
        device_enabled_pattern.setObjectName("ankihaptics_device_enabled_pattern")
        device_enabled_pattern_box.addWidget(device_enabled_pattern)
        general_tab_vertical_layout.addLayout(device_enabled_pattern_box)

        actuators_label = QLabel("Actuators:")
        general_tab_vertical_layout.addWidget(actuators_label)

        for config_actuator in config["devices"][device_index]["actuators"]:
            device_actuator_enabled_box = QGroupBox(config_actuator["name"])
            device_actuator_enabled_box.setCheckable(True)
            device_actuator_enabled_box.setChecked(config_actuator["enabled"])
            device_actuator_enabled_box.setObjectName("ankihaptics_actuator_" + str(config_actuator["index"]))
            device_actuator_enabled_box_layout = QVBoxLayout()

            device_actuator_strength_multiplier_box = QHBoxLayout()
            device_actuator_strength_multiplier_box.addWidget(QLabel("Strength Multiplier"))
            device_actuator_strength_multiplier = QLineEdit()
            device_actuator_strength_multiplier.setText(str(config_actuator["strength_multiplier"]))
            device_actuator_strength_multiplier.setObjectName("ankihaptics_actuator_" + str(config_actuator["index"]) + "_strength_multiplier")
            device_actuator_strength_multiplier_box.addWidget(device_actuator_strength_multiplier)
            device_actuator_enabled_box_layout.addLayout(device_actuator_strength_multiplier_box)

            device_actuator_enabled_box.setLayout(device_actuator_enabled_box_layout)
            general_tab_vertical_layout.addWidget(device_actuator_enabled_box)


        #Answer Buttons Tab
        anki_actions_tab = QWidget()
        anki_actions_tab_scroll_area = QScrollArea()
        anki_actions_tab_scroll_area.setWidgetResizable(True)
        anki_actions_tab_vertical_layout = QVBoxLayout()
        anki_actions_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        anki_actions_tab.setLayout(anki_actions_tab_vertical_layout)
        anki_actions_tab_scroll_area.setWidget(anki_actions_tab)
        tabs_frame.addTab(anki_actions_tab_scroll_area, "Anki Actions")

        anki_actions_settings = [
            {"display_name": "Again Button", "config_name": "again"},
            {"display_name": "Hard Button", "config_name": "hard"},
            {"display_name": "Good Button", "config_name": "good"},
            {"display_name": "Easy Button", "config_name": "easy"},
            {"display_name": "Show Question", "config_name": "show_question"},
            {"display_name": "Show Answer", "config_name": "show_answer"},
        ]

        for anki_action_setting in anki_actions_settings:
            anki_action_box = QGroupBox(anki_action_setting["display_name"])
            anki_action_box.setCheckable(True)
            anki_action_box.setChecked(config["devices"][device_index][anki_action_setting["config_name"]]["enabled"])
            anki_action_box.setObjectName("ankihaptics_" + anki_action_setting["config_name"] + "_box")
            anki_action_box_layout = QVBoxLayout()

            anki_action_strength_box = QHBoxLayout()
            anki_action_strength_box.addWidget(QLabel("Strength"))
            anki_action_strength = QSlider(Qt.Orientation.Horizontal)
            anki_action_strength.setValue(int(config["devices"][device_index][anki_action_setting["config_name"]]["strength"] * 100))
            anki_action_strength.setObjectName("ankihaptics_" + anki_action_setting["config_name"] + "_strength")
            anki_action_strength_box.addWidget(anki_action_strength)
            anki_action_box_layout.addLayout(anki_action_strength_box)

            anki_action_box.setLayout(anki_action_box_layout)
            anki_actions_tab_vertical_layout.addWidget(anki_action_box)


        #Duration Tab
        duration_tab = QWidget()
        duration_tab_scroll_area = QScrollArea()
        duration_tab_scroll_area.setWidgetResizable(True)
        duration_tab_vertical_layout = QVBoxLayout()
        duration_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        duration_info_label = QLabel("Durations apply to all connected devices")
        duration_tab_vertical_layout.addWidget(duration_info_label)
        duration_info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        for anki_action_duration_setting in anki_actions_settings:
            anki_action_duration_box = QHBoxLayout()
            anki_action_duration_box.addWidget(QLabel(anki_action_duration_setting["display_name"]))
            anki_action_duration = QLineEdit()
            anki_action_duration.setText(str(config["duration"][anki_action_duration_setting["config_name"]]))
            anki_action_duration.setObjectName("ankihaptics_" + anki_action_duration_setting["config_name"] + "_duration")
            anki_action_duration_box.addWidget(anki_action_duration)
            anki_action_duration_box.addWidget(QLabel("seconds"))

            duration_tab_vertical_layout.addLayout(anki_action_duration_box)

        duration_tab.setLayout(duration_tab_vertical_layout)
        duration_tab_scroll_area.setWidget(duration_tab)
        tabs_frame.addTab(duration_tab_scroll_area, "Duration")


        #Streaks Tab
        anki_streak_actions_settings = [
            {"display_name": "Again Button", "config_name": "again"},
            {"display_name": "Hard Button", "config_name": "hard"},
            {"display_name": "Good Button", "config_name": "good"},
            {"display_name": "Easy Button", "config_name": "easy"},
        ]

        streaks_tab = QWidget()
        streaks_tab_scroll_area = QScrollArea()
        streaks_tab_scroll_area.setWidgetResizable(True)
        streaks_tab_vertical_layout = QVBoxLayout()
        streaks_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        streaks_info_label = QLabel("Streaks apply to all connected devices")
        streaks_tab_vertical_layout.addWidget(streaks_info_label)
        streaks_info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        streak_type_horizontal_layout = QHBoxLayout()
        streak_type_combobox = QComboBox()
        streak_types = ["Per Collection", "Per Deck", "Per Card"]
        streak_type_combobox.addItems(streak_types)
        streak_type_combobox.setCurrentText(config["streak"]["streak_type"])
        streak_type_combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        streak_type_combobox.setObjectName("ankihaptics_streak_type")
        streak_type_horizontal_layout.addWidget(QLabel("Streak Type: "))
        streak_type_horizontal_layout.addWidget(streak_type_combobox)
        streaks_tab_vertical_layout.addLayout(streak_type_horizontal_layout)

        for anki_streak_actions_setting in anki_streak_actions_settings:
            anki_streak_action_box = QGroupBox(anki_streak_actions_setting["display_name"])
            anki_streak_action_box.setCheckable(True)
            anki_streak_action_box.setChecked(config["streak"][anki_streak_actions_setting["config_name"]]["enabled"])
            anki_streak_action_box.setObjectName("ankihaptics_streak_" + anki_streak_actions_setting["config_name"] + "_box")
            anki_streak_action_box_layout = QVBoxLayout()

            anki_streak_action_strength_box = QHBoxLayout()
            anki_streak_action_strength_box.addWidget(QLabel("Strength"))
            anki_streak_action_strength = QLineEdit()
            anki_streak_action_strength.setText(str(config["streak"][anki_streak_actions_setting["config_name"]]["strength"]))
            anki_streak_action_strength.setObjectName("ankihaptics_streak_" + anki_streak_actions_setting["config_name"] + "_strength")
            anki_streak_action_strength_box.addWidget(anki_streak_action_strength)
            anki_streak_action_box_layout.addLayout(anki_streak_action_strength_box)

            anki_streak_action_duration_box = QHBoxLayout()
            anki_streak_action_duration_box.addWidget(QLabel("Duration"))
            anki_streak_action_duration = QLineEdit()
            anki_streak_action_duration.setText(str(config["streak"][anki_streak_actions_setting["config_name"]]["duration"]))
            anki_streak_action_duration.setObjectName("ankihaptics_streak_" + anki_streak_actions_setting["config_name"] + "_duration")
            anki_streak_action_duration_box.addWidget(anki_streak_action_duration)
            anki_streak_action_box_layout.addLayout(anki_streak_action_duration_box)

            anki_streak_action_box.setLayout(anki_streak_action_box_layout)
            streaks_tab_vertical_layout.addWidget(anki_streak_action_box)

        anki_streak_min_box = QHBoxLayout()
        anki_streak_min_box.addWidget(QLabel("Minimum Length"))
        anki_streak_min = QLineEdit()
        anki_streak_min.setText(str(config["streak"]["min_length"]))
        anki_streak_min.setObjectName("ankihaptics_streak_min")
        anki_streak_min_box.addWidget(anki_streak_min)
        anki_streak_min_box.addWidget(QLabel("cards"))
        streaks_tab_vertical_layout.addLayout(anki_streak_min_box)

        anki_streak_max_box = QHBoxLayout()
        anki_streak_max_box.addWidget(QLabel("Maximum Length"))
        anki_streak_max = QLineEdit()
        anki_streak_max.setText(str(config["streak"]["max_length"]))
        anki_streak_max.setObjectName("ankihaptics_streak_max")
        anki_streak_max_box.addWidget(anki_streak_max)
        anki_streak_max_box.addWidget(QLabel("cards"))
        streaks_tab_vertical_layout.addLayout(anki_streak_max_box)

        anki_streak_time_box = QHBoxLayout()
        anki_streak_time_box.addWidget(QLabel("Maximum Time"))
        anki_streak_time = QLineEdit()
        anki_streak_time.setText(str(config["streak"]["streak_time_epoch_ms"] / 60000))
        anki_streak_time.setObjectName("ankihaptics_streak_time")
        anki_streak_time_box.addWidget(anki_streak_time)
        anki_streak_time_box.addWidget(QLabel("minutes"))
        streaks_tab_vertical_layout.addLayout(anki_streak_time_box)

        streaks_tab.setLayout(streaks_tab_vertical_layout)
        streaks_tab_scroll_area.setWidget(streaks_tab)
        tabs_frame.addTab(streaks_tab_scroll_area, "Streaks")


        #Test Tab
        test_tab = QWidget()
        test_tab_scroll_area = QScrollArea()
        test_tab_scroll_area.setWidgetResizable(True)
        test_tab_vertical_layout = QVBoxLayout()
        test_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        test_info_label = QLabel("Save your settings before running tests.")
        test_tab_vertical_layout.addWidget(test_info_label)
        test_info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        test_type_horizontal_layout = QHBoxLayout()
        test_type_combobox = QComboBox()
        test_types = [*(x["display_name"] for x in anki_actions_settings)]
        test_type_combobox.addItems(test_types)
        test_type_combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        test_type_horizontal_layout.addWidget(QLabel("Test Action: "))
        test_type_horizontal_layout.addWidget(test_type_combobox)
        test_tab_vertical_layout.addLayout(test_type_horizontal_layout)

        def run_test() -> None:
            hook = [anki_actions_setting["config_name"] for anki_actions_setting in anki_actions_settings if anki_actions_setting["display_name"] == test_type_combobox.currentText()][0]

            config = config_util.ensure_device_settings(config_util.get_config(aqt.mw), self.client.devices)
            devices = self.client.devices
            config_device = config["devices"][device_index]
            websocket_command = {"command": "scalar_cmd", "args": {"devices": []}}

            if not config_device[hook]["enabled"]:
                return

            client_device = None
            try:
                client_device = [device for device in devices.values() if device.name == config_device["device_name"]][0] #should only return one device
            except Exception:  # noqa: BLE001
                logger.error_log("Hook failed to find device", traceback.format_exc())
                return

            enabled_actuators = []
            for device_actuator in client_device.actuators:
                for config_actuator in config_device["actuators"]:
                    if config_actuator["index"] == device_actuator.index and config_actuator["enabled"]:
                        enabled_actuators.append(device_actuator)

            if len(enabled_actuators) > 0:
                command_strength = config_device[hook]["strength"]
                command_duration = config["duration"][hook]
                websocket_command["args"]["devices"].append({"index": client_device.index, "actuators": enabled_actuators, "strength": command_strength})
                websocket_command["args"]["duration"] = command_duration

            self.websocket_command_queue.append(websocket_command)

        test_button = QPushButton("Run Test", clicked = run_test)
        test_tab_vertical_layout.addWidget(test_button)

        test_tab.setLayout(test_tab_vertical_layout)
        test_tab_scroll_area.setWidget(test_tab)
        tabs_frame.addTab(test_tab_scroll_area, "Test")
