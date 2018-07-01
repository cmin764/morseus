"""Morseus default settings and constants."""


import os

from libmorse import UNIT


# Basic camera image and color processing options.
SECOND = 1000.0    # how much is a second in ms
UNIT = float(UNIT)    # default morse unit (explicit declare)
MAX_FPS = 30    # maximum number of frames per second supported
FPS_FACTOR = 3    # multiplied with the lowest computed FPS value
TIME_DELTA = False    # use own computed time difference

# Pixels above this threshold are considered white.
MONO_THRESHOLD = 250
LIGHT_DARK_RATIO = 1.0    # minimum light vs. dark quantity in an image
BOUNDING_BOX = True    # crop empty areas when light is detected
BOX_MIN_RATIO = 0.01    # minimum area ratio between box and source
SPOT_NOISE_RATIO = 0.1    # maximum area ratio between any and the main spot
SPOT_MIN_RATIO = BOX_MIN_RATIO / 2    # main spot minimum accepted area

# Sub-area of interest within the whole capture.
class AREA:
    # How smaller is comparing to original.
    RATIO = 1.0 / 3
    # Minimum and maximum width for a sub-area.
    class WIDTH:
        MIN = 100.0
        MAX = 500.0

# Choose from different camera providers.
class CAMERA_PROVIDERS:
    AVFOUNDATION = "avfoundation"
    ANDROID = "android"
    PICAMERA = "picamera"
    GI = "gi"
    OPENCV = "opencv"

    ENABLE = True
    IMPLICIT = {
        "linux": OPENCV,
        "macosx": AVFOUNDATION,
        "win": OPENCV,
    }
    EXPLICIT = None

# Logging implicit options.
class LOGGING:
    USE = True    # use logging
    DEBUG = True    # show debug messages

    class FILE:    # use a logging file or not
        IMPLICIT = {
            "linux": True,
            "macosx": True,
            "win": True,
            "android": False,
        }
        EXPLICIT = None

# Project directory (package parent).
PROJECT = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        os.path.pardir
    )
)
ICON = os.path.join(PROJECT, "artwork", "morseus.ico")
