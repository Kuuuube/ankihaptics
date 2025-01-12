import asyncio
import logging
import threading
import time

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

from . import config_util, hooks, util


class AnkiHaptics:
    def __init__(self, mw: aqt.main.AnkiQt) -> None:
        if mw:
            config = config_util.get_config(mw)

            self.menuAction = QAction("Anki Haptics Settings", mw, triggered = lambda: self._setup_settings_window(config))
            mw.form.menuTools.addSeparator()
            mw.form.menuTools.addAction(self.menuAction)

            self.client = None
            self.keep_websocket_thread_alive = True
            self.websocket_command = {"command": None}
            self.websocket_status = "NOT_STARTED"
            self.websocket_thread = None
            self._start_websocket_thread(config)

            #Prevent Anki from hanging forever due to infinitely running thread
            aqt.gui_hooks.profile_will_close.append(self._cleanup)

    def _start_websocket_thread(self, config: dict) -> None:
        websocket_thread = threading.Thread(target = lambda: util.start_async(lambda: self._start_websocket(config)))
        websocket_thread.start()
        self.websocket_thread = websocket_thread

    def _cleanup(self) -> None:
        self.keep_websocket_thread_alive = False

    async def _start_websocket(self, config: dict) -> None:
        self.client = Client("Anki Haptics Client", ProtocolSpec.v3)
        self.websocket_status = "STARTING"
        connector = WebsocketConnector(config["websocket_path"], logger = self.client.logger)

        try:
            await self.client.connect(connector)
            self.websocket_status = "OK"
        except Exception as e:
            self.websocket_status = "ERROR\n" + str(e)
            logging.exception("Could not connect to server, exiting")
            return

        self.client.logger.info("Devices: " + str(self.client.devices))

        hooks.register_hooks(aqt.mw, self)

        currently_scanning = False
        while self.keep_websocket_thread_alive:
            if self.websocket_command["command"] == "start_scanning" and not currently_scanning:
                await self.client.start_scanning()
                currently_scanning = True
            elif self.websocket_command["command"] == "stop_scanning" and currently_scanning:
                await self.client.stop_scanning()
                currently_scanning = False
            elif self.websocket_command["command"] == "scalar_cmd":
                for device in self.websocket_command["args"]["devices"]:
                    for actuator in device["actuators"]:
                        await actuator.command(device["strength"])
                    await asyncio.sleep(device["duration"])
                    for actuator in device["actuators"]:
                        await actuator.command(0.0)

                self.websocket_command["command"] = None

            await asyncio.sleep(config["websocket_polling_delay_ms"] / 1000)

        await self.client.disconnect()
        self.websocket_status = "DISCONNECTED"

    def _setup_settings_window(self, config: dict) -> None:
        if self.client:
            config = config_util.ensure_device_settings(config, self.client.devices)
        settings_window = QDialog(aqt.mw)
        vertical_layout = QVBoxLayout()

        def trigger_websocket_reconnect() -> None:
            while self.websocket_thread and self.websocket_thread.is_alive():
                self.keep_websocket_thread_alive = False
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
            if self.websocket_command["command"] != "start_scanning":
                scan_button.setText("Stop Scanning for Devices")
                self.websocket_command["command"] = "start_scanning"
            elif self.websocket_command["command"] == "start_scanning":
                scan_button.setText("Scan for Devices")
                self.websocket_command["command"] = "stop_scanning"

        if self.websocket_status != "OK" or not self.client:
            vertical_layout.addWidget(QLabel("Failed to connect to websocket. Status code: " + self.websocket_status))
            reconnect_button = QPushButton("Reconnect", clicked = trigger_websocket_reconnect)
            vertical_layout.addWidget(reconnect_button)
            settings_window.setLayout(vertical_layout)
            settings_window.resize(500, 400)
            if settings_window.exec():
                settings_window.show()
            return

        scan_button_text = "Scan for Devices" if self.websocket_command["command"] != "start_scanning" else "Stop Scanning for Devices"

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
                "enabled_pattern": tabs_frame.findChild(QLineEdit, "ankihaptics_device_enabled_pattern").text(),
                "again": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_again_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_again_strength").value() / 99, 2),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_again_duration").text(), 0.0),
                },
                "hard": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_hard_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_hard_strength").value() / 99, 2),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_hard_duration").text(), 0.0),
                },
                "good": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_good_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_good_strength").value() / 99, 2),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_good_duration").text(), 0.0),
                },
                "easy": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_easy_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_easy_strength").value() / 99, 2),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_easy_duration").text(), 0.0),
                },
                "show_question": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_show_question_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_show_question_strength").value() / 99, 2),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_show_question_duration").text(), 0.0),
                },
                "show_answer": {
                    "enabled": tabs_frame.findChild(QGroupBox, "ankihaptics_show_answer_box").isChecked(),
                    "strength": round(tabs_frame.findChild(QSlider, "ankihaptics_show_answer_strength").value() / 99, 2),
                    "duration": util.maybe_parse_float(tabs_frame.findChild(QLineEdit, "ankihaptics_show_answer_duration").text(), 0.0),
                },
            }
            config_util.set_config(aqt.mw, config)
            return config

        bottom_buttons_horizontal_layout = QHBoxLayout()
        vertical_layout.addLayout(bottom_buttons_horizontal_layout)
        generate_button = QPushButton("Save", clicked = lambda _: _set_config_attributes(config, get_device_index(config, devices_combobox.currentText())))
        bottom_buttons_horizontal_layout.addWidget(generate_button)
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

            anki_action_duration_box = QHBoxLayout()
            anki_action_duration_box.addWidget(QLabel("Duration"))
            anki_action_duration = QLineEdit()
            anki_action_duration.setText(str(config["devices"][device_index][anki_action_setting["config_name"]]["duration"]))
            anki_action_duration.setObjectName("ankihaptics_" + anki_action_setting["config_name"] + "_duration")
            anki_action_duration_box.addWidget(anki_action_duration)
            anki_action_duration_box.addWidget(QLabel("seconds"))
            anki_action_box_layout.addLayout(anki_action_duration_box)

            anki_action_box.setLayout(anki_action_box_layout)
            anki_actions_tab_vertical_layout.addWidget(anki_action_box)


        #Advanced Tab
        advanced_tab = QWidget()
        advanced_tab_scroll_area = QScrollArea()
        advanced_tab_scroll_area.setWidgetResizable(True)
        advanced_tab_vertical_layout = QVBoxLayout()
        advanced_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        advanced_tab.setLayout(advanced_tab_vertical_layout)
        advanced_tab_scroll_area.setWidget(advanced_tab)
        tabs_frame.addTab(advanced_tab_scroll_area, "Advanced")
