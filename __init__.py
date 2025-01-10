#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if __name__ != "__main__" and "pytest" not in sys.modules:
    from aqt import mw
    from . import ankiplug
    # Save a reference to the toolkit onto the mw, preventing garbage collection of PyQt objects
    if mw:
        mw.ankiplug = ankiplug.AnkiPlug(mw)
else:
    print("This is an addon for the Anki spaced repetition learning system and cannot be run directly.")
    print("Please download Anki from <https://apps.ankiweb.net/>")
