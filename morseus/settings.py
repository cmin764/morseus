"""Morseus default settings and constants."""


from libmorse import UNIT


# Camera image processing options.
SECOND = 1000.0    # how much is a second in in ms
UNIT = float(UNIT)    # default morse unit (explicit declare)

# Sub-area of interest within the whole capture.
class AREA:
    # How smaller is it.
    RATIO = 0.2
    # Minimum and maximum width for a sub-area.
    class WIDTH:
        MIN = 100.0
        MAX = 200.0
