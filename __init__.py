#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if __name__ != "__main__" and "pytest" not in sys.modules:
    from . import ankiplug
    ankiplug.register_hooks()
else:
    print("This is an addon for the Anki spaced repetition learning system and cannot be run directly.")
    print("Please download Anki from <https://apps.ankiweb.net/>")
