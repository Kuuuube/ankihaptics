import types
import asyncio
import logging
import threading

from aqt import mw, gui_hooks
from aqt.qt import (Qt, QAction, QDialog, QVBoxLayout, QHBoxLayout,
                    QComboBox, QSizePolicy, QLabel, QTabWidget, QWidget,
                    QScrollArea, QPushButton, QCheckBox, QSlider, QLineEdit,
                    QGroupBox)
from buttplug import Client, WebsocketConnector, ProtocolSpec

from . import hooks, config_util, util

class AnkiHaptics:
    def __init__(self, mw):
        if mw:
            self.config = types.SimpleNamespace(**config_util.get_config(mw))

            self.menuAction = QAction("Anki Haptics Settings", mw, triggered = self.setup_settings_window)
            mw.form.menuTools.addSeparator()
            mw.form.menuTools.addAction(self.menuAction)

            self.client = None
            threading.Thread(target = lambda: util.start_async(self.get_devices)).start()

            #Prevent Anki from hanging forever due to infinitely running thread
            self.keep_websocket_thread_alive = True
            gui_hooks.profile_will_close.append(self.cleanup)

    def cleanup(self):
        self.keep_websocket_thread_alive = False

    async def get_devices(self):
        self.client = Client("Anki Haptics Client", ProtocolSpec.v3)
        connector = WebsocketConnector(self.config.websocket_path, logger = self.client.logger)

        try:
            await self.client.connect(connector)
        except Exception as e:
            logging.error(f"Could not connect to server, exiting: {e}")
            return

        await self.client.start_scanning()
        await asyncio.sleep(5)
        await self.client.stop_scanning()

        self.client.logger.info(f"Devices: {self.client.devices}")

        hooks.register_hooks(mw, self.client)

        while self.keep_websocket_thread_alive:
            await asyncio.sleep(1)

        await self.client.disconnect()

    def setup_settings_window(self):
        config = self.config

        settings_window = QDialog(mw)
        vertical_layout = QVBoxLayout()

        default_device_name = "*"

        #Above Tabs
        devices_horizontal_layout = QHBoxLayout()
        devices_combobox = QComboBox()
        devices_combobox.addItems([*((x["device_name"]) for x in config.devices)])
        devices_combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        devices_horizontal_layout.addWidget(QLabel("Device: "))
        devices_combobox.setCurrentText(default_device_name)
        def get_device_index(config, device_name):
            for i, device in enumerate(config.devices):
                if device["device_name"] == device_name:
                    return i
            return 0
        def update_vertical_layout_tabs(device_name):
            current_tab = tabs_frame.currentIndex()
            tab_count = tabs_frame.count()
            for tab_index in reversed(range(tab_count)):
                tabs_frame.widget(tab_index).deleteLater()
            self.setup_vertical_layout_tabs(config, tabs_frame, get_device_index(config, device_name))
            tabs_frame.setCurrentIndex(current_tab)
        devices_combobox.currentTextChanged.connect(update_vertical_layout_tabs)

        devices_horizontal_layout.addWidget(devices_combobox)
        vertical_layout.addLayout(devices_horizontal_layout)

        tabs_frame = QTabWidget()
        vertical_layout.addWidget(tabs_frame)

        self.setup_vertical_layout_tabs(config, tabs_frame, get_device_index(config, default_device_name))

        #Bottom Buttons
        def set_config_attributes(config, device_index, write_to_anki = False):
            config.devices[device_index] = {
                "device_name": config.devices[device_index]["device_name"],
                "enabled_by_default": mw.findChild(QCheckBox, "ankihaptics_device_enabled").isChecked(),
                "enabled_pattern": mw.findChild(QLineEdit, "ankihaptics_device_enabled_pattern").text(),
                "again": {
                    "enabled": mw.findChild(QGroupBox, "ankihaptics_again_button_box").isChecked(),
                    "strength": round(mw.findChild(QSlider, "ankihaptics_again_button_strength").value() / 99, 2),
                    "duration": util.try_parse_float(mw.findChild(QLineEdit, "ankihaptics_again_button_duration").text()),
                },
                "hard": {
                    "enabled": mw.findChild(QGroupBox, "ankihaptics_hard_button_box").isChecked(),
                    "strength": round(mw.findChild(QSlider, "ankihaptics_hard_button_strength").value() / 99, 2),
                    "duration": util.try_parse_float(mw.findChild(QLineEdit, "ankihaptics_hard_button_duration").text()),
                },
                "good": {
                    "enabled": mw.findChild(QGroupBox, "ankihaptics_good_button_box").isChecked(),
                    "strength": round(mw.findChild(QSlider, "ankihaptics_good_button_strength").value() / 99, 2),
                    "duration": util.try_parse_float(mw.findChild(QLineEdit, "ankihaptics_good_button_duration").text()),
                },
                "easy": {
                    "enabled": mw.findChild(QGroupBox, "ankihaptics_easy_button_box").isChecked(),
                    "strength": round(mw.findChild(QSlider, "ankihaptics_easy_button_strength").value() / 99, 2),
                    "duration": util.try_parse_float(mw.findChild(QLineEdit, "ankihaptics_easy_button_duration").text()),
                }
            }
            if write_to_anki:
                config_util.set_config(mw, config)
            return config

        bottom_buttons_horizontal_layout = QHBoxLayout()
        vertical_layout.addLayout(bottom_buttons_horizontal_layout)
        generate_button = QPushButton("Save", clicked = lambda _: set_config_attributes(config, get_device_index(config, devices_combobox.currentText()), write_to_anki = True))
        bottom_buttons_horizontal_layout.addWidget(generate_button)
        close_button = QPushButton("Close", clicked = settings_window.reject)
        bottom_buttons_horizontal_layout.addWidget(close_button)

        settings_window.setLayout(vertical_layout)
        settings_window.resize(500, 400)
        if settings_window.exec():
            settings_window.show()


    def setup_vertical_layout_tabs(self, config, tabs_frame, device_index):
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
        device_enabled.setChecked(config.devices[device_index]["enabled_by_default"])
        general_tab_vertical_layout.addWidget(device_enabled)

        device_enabled_pattern_box = QHBoxLayout()
        device_enabled_pattern_box.addWidget(QLabel("Enabled Pattern"))
        device_enabled_pattern = QLineEdit()
        device_enabled_pattern.setText(str(config.devices[device_index]["enabled_pattern"]))
        device_enabled_pattern.setObjectName("ankihaptics_device_enabled_pattern")
        device_enabled_pattern_box.addWidget(device_enabled_pattern)
        general_tab_vertical_layout.addLayout(device_enabled_pattern_box)


        #Answer Buttons Tab
        answer_buttons_tab = QWidget()
        answer_buttons_tab_scroll_area = QScrollArea()
        answer_buttons_tab_scroll_area.setWidgetResizable(True)
        answer_buttons_tab_vertical_layout = QVBoxLayout()
        answer_buttons_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        answer_buttons_tab.setLayout(answer_buttons_tab_vertical_layout)
        answer_buttons_tab_scroll_area.setWidget(answer_buttons_tab)
        tabs_frame.addTab(answer_buttons_tab_scroll_area, "Answer Buttons")

        #Again Button Settings
        again_button_box = QGroupBox("Again Button")
        again_button_box.setCheckable(True)
        again_button_box.setChecked(config.devices[device_index]["again"]["enabled"])
        again_button_box.setObjectName("ankihaptics_again_button_box")
        again_button_box_layout = QVBoxLayout()

        again_button_strength_box = QHBoxLayout()
        again_button_strength_box.addWidget(QLabel("Strength"))
        again_button_strength = QSlider(Qt.Orientation.Horizontal)
        again_button_strength.setValue(int(config.devices[device_index]["again"]["strength"] * 100))
        again_button_strength.setObjectName("ankihaptics_again_button_strength")
        again_button_strength_box.addWidget(again_button_strength)
        again_button_box_layout.addLayout(again_button_strength_box)

        again_button_duration_box = QHBoxLayout()
        again_button_duration_box.addWidget(QLabel("Duration"))
        again_button_duration = QLineEdit()
        again_button_duration.setText(str(config.devices[device_index]["again"]["duration"]))
        again_button_duration.setObjectName("ankihaptics_again_button_duration")
        again_button_duration_box.addWidget(again_button_duration)
        again_button_duration_box.addWidget(QLabel("seconds"))
        again_button_box_layout.addLayout(again_button_duration_box)

        again_button_box.setLayout(again_button_box_layout)
        answer_buttons_tab_vertical_layout.addWidget(again_button_box)

        #Hard Button Settings
        hard_button_box = QGroupBox("Hard Button")
        hard_button_box.setCheckable(True)
        hard_button_box.setChecked(config.devices[device_index]["hard"]["enabled"])
        hard_button_box.setObjectName("ankihaptics_hard_button_box")
        hard_button_box_layout = QVBoxLayout()

        hard_button_strength_box = QHBoxLayout()
        hard_button_strength_box.addWidget(QLabel("Strength"))
        hard_button_strength = QSlider(Qt.Orientation.Horizontal)
        hard_button_strength.setValue(int(config.devices[device_index]["hard"]["strength"] * 100))
        hard_button_strength.setObjectName("ankihaptics_hard_button_strength")
        hard_button_strength_box.addWidget(hard_button_strength)
        hard_button_box_layout.addLayout(hard_button_strength_box)

        hard_button_duration_box = QHBoxLayout()
        hard_button_duration_box.addWidget(QLabel("Duration"))
        hard_button_duration = QLineEdit()
        hard_button_duration.setText(str(config.devices[device_index]["hard"]["duration"]))
        hard_button_duration.setObjectName("ankihaptics_hard_button_duration")
        hard_button_duration_box.addWidget(hard_button_duration)
        hard_button_duration_box.addWidget(QLabel("seconds"))
        hard_button_box_layout.addLayout(hard_button_duration_box)

        hard_button_box.setLayout(hard_button_box_layout)
        answer_buttons_tab_vertical_layout.addWidget(hard_button_box)

        #Good Button Settings
        good_button_box = QGroupBox("Good Button")
        good_button_box.setCheckable(True)
        good_button_box.setChecked(config.devices[device_index]["good"]["enabled"])
        good_button_box.setObjectName("ankihaptics_good_button_box")
        good_button_box_layout = QVBoxLayout()

        good_button_strength_box = QHBoxLayout()
        good_button_strength_box.addWidget(QLabel("Strength"))
        good_button_strength = QSlider(Qt.Orientation.Horizontal)
        good_button_strength.setValue(int(config.devices[device_index]["good"]["strength"] * 100))
        good_button_strength.setObjectName("ankihaptics_good_button_strength")
        good_button_strength_box.addWidget(good_button_strength)
        good_button_box_layout.addLayout(good_button_strength_box)

        good_button_duration_box = QHBoxLayout()
        good_button_duration_box.addWidget(QLabel("Duration"))
        good_button_duration = QLineEdit()
        good_button_duration.setText(str(config.devices[device_index]["good"]["duration"]))
        good_button_duration.setObjectName("ankihaptics_good_button_duration")
        good_button_duration_box.addWidget(good_button_duration)
        good_button_duration_box.addWidget(QLabel("seconds"))
        good_button_box_layout.addLayout(good_button_duration_box)

        good_button_box.setLayout(good_button_box_layout)
        answer_buttons_tab_vertical_layout.addWidget(good_button_box)

        #Easy Button Settings
        easy_button_box = QGroupBox("Easy Button")
        easy_button_box.setCheckable(True)
        easy_button_box.setChecked(config.devices[device_index]["easy"]["enabled"])
        easy_button_box.setObjectName("ankihaptics_easy_button_box")
        easy_button_box_layout = QVBoxLayout()

        easy_button_strength_box = QHBoxLayout()
        easy_button_strength_box.addWidget(QLabel("Strength"))
        easy_button_strength = QSlider(Qt.Orientation.Horizontal)
        easy_button_strength.setValue(int(config.devices[device_index]["easy"]["strength"] * 100))
        easy_button_strength.setObjectName("ankihaptics_easy_button_strength")
        easy_button_strength_box.addWidget(easy_button_strength)
        easy_button_box_layout.addLayout(easy_button_strength_box)

        easy_button_duration_box = QHBoxLayout()
        easy_button_duration_box.addWidget(QLabel("Duration"))
        easy_button_duration = QLineEdit()
        easy_button_duration.setText(str(config.devices[device_index]["easy"]["duration"]))
        easy_button_duration.setObjectName("ankihaptics_easy_button_duration")
        easy_button_duration_box.addWidget(easy_button_duration)
        easy_button_duration_box.addWidget(QLabel("seconds"))
        easy_button_box_layout.addLayout(easy_button_duration_box)

        easy_button_box.setLayout(easy_button_box_layout)
        answer_buttons_tab_vertical_layout.addWidget(easy_button_box)


        #Advanced Tab
        advanced_tab = QWidget()
        advanced_tab_scroll_area = QScrollArea()
        advanced_tab_scroll_area.setWidgetResizable(True)
        advanced_tab_vertical_layout = QVBoxLayout()
        advanced_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        advanced_tab.setLayout(advanced_tab_vertical_layout)
        advanced_tab_scroll_area.setWidget(advanced_tab)
        tabs_frame.addTab(advanced_tab_scroll_area, "Advanced")
