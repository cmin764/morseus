"""Morseus default settings and constants."""


from libmorse import UNIT


# Basic camera image and color processing options.
SECOND = 1000.0    # how much is a second in ms
UNIT = float(UNIT)    # default morse unit (explicit declare)
MAX_FPS = 30    # maximum number of frames per second supported
FPS_FACTOR = 3    # multiplied with the lowest computed FPS value

MONO_THRESHOLD = 250    # pixels above this are considered white
LIGHT_DARK_RATIO = 1.0    # minimum light vs. dark quantity in an image
BOUNDING_BOX = True    # crop empty areas when light is detected
BOX_MIN_RATIO = 0.2    # minimum area ratio between box and source

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
    EXPLICIT = OPENCV
