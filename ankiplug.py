import types

from aqt import mw
from aqt.qt import (Qt, QAction, QDialog, QVBoxLayout, QHBoxLayout,
                    QComboBox, QSizePolicy, QLabel, QTabWidget, QWidget,
                    QScrollArea, QPushButton, QCheckBox)

from . import hooks, config_util

class AnkiPlug:
    def __init__(self, mw):
        if mw:
            self.menuAction = QAction("AnkiPlug Settings", mw, triggered = self.setup_settings_window)
            mw.form.menuTools.addSeparator()
            mw.form.menuTools.addAction(self.menuAction)

            hooks.register_hooks(mw)

    def setup_settings_window(self):
        config = types.SimpleNamespace(**config_util.get_config(mw))

        settings_window = QDialog(mw)
        vertical_layout = QVBoxLayout()

        #Above Tabs
        deck_horizontal_layout = QHBoxLayout()
        devices_combobox = QComboBox()
        devices_combobox.addItem("*") # * = all devices
        devices_combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        deck_horizontal_layout.addWidget(QLabel("Device: "))
        devices_combobox.setCurrentText("*")

        deck_horizontal_layout.addWidget(devices_combobox)
        vertical_layout.addLayout(deck_horizontal_layout)

        tabs_frame = QTabWidget()
        vertical_layout.addWidget(tabs_frame)

        #General Tab
        general_tab = QWidget()
        general_tab_scroll_area = QScrollArea()
        general_tab_scroll_area.setWidgetResizable(True)
        general_tab_vertical_layout = QVBoxLayout()
        general_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        device_enabled = QCheckBox("Device Enabled")
        # device_enabled.setChecked(config.enabled)
        general_tab_vertical_layout.addWidget(device_enabled)

        general_tab.setLayout(general_tab_vertical_layout)
        general_tab_scroll_area.setWidget(general_tab)
        tabs_frame.addTab(general_tab_scroll_area, "General")

        #Advanced Tab
        advanced_tab = QWidget()
        advanced_tab_scroll_area = QScrollArea()
        advanced_tab_scroll_area.setWidgetResizable(True)
        advanced_tab_vertical_layout = QVBoxLayout()
        advanced_tab_vertical_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        advanced_tab.setLayout(advanced_tab_vertical_layout)
        advanced_tab_scroll_area.setWidget(advanced_tab)
        tabs_frame.addTab(advanced_tab_scroll_area, "Advanced")

        #Bottom Buttons
        bottom_buttons_horizontal_layout = QHBoxLayout()
        vertical_layout.addLayout(bottom_buttons_horizontal_layout)
        generate_button = QPushButton("Save", clicked = settings_window.accept)
        bottom_buttons_horizontal_layout.addWidget(generate_button)
        close_button = QPushButton("Close", clicked = settings_window.reject)
        bottom_buttons_horizontal_layout.addWidget(close_button)

        def set_config_attributes(config):
            return config

        settings_window.setLayout(vertical_layout)
        settings_window.resize(500, 400)
        if settings_window.exec():
            mw.progress.start(immediate = True)
            config = set_config_attributes(config)
            mw.progress.finish()
            self.win.show()
