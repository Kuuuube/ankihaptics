from aqt.qt import QAction

from . import hooks

class AnkiPlug:
    def __init__(self, mw):
        if mw:
            self.menuAction = QAction("AnkiPlug Settings", mw, triggered = self.setup_options_window)
            mw.form.menuTools.addSeparator()
            mw.form.menuTools.addAction(self.menuAction)

            hooks.register_hooks(mw)

    def setup_options_window(self):
        pass
