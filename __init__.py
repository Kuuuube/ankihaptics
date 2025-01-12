import os
import sys

# add lib folder to path to allow accessing modules there
sys.path.append(os.path.dirname(__file__) + "/lib")

if __name__ != "__main__" and "pytest" not in sys.modules:
    import aqt

    from . import ankihaptics
    # Save a reference to the toolkit onto the mw, preventing garbage collection of PyQt objects
    if aqt.mw:
        aqt.mw.ankihaptics = ankihaptics.AnkiHaptics(aqt.mw)
else:
    print("This is an addon for the Anki spaced repetition learning system and cannot be run directly.\nPlease download Anki from <https://apps.ankiweb.net/>")  # noqa: T201
