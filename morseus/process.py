"""Process images into timed Morse signals."""


import collections

from morseus import settings


class Decoder(object):

    """Interpret black & white images as Morse code."""

    BW_MODE = "L"
    MONO_MODE = "1"
    MONO_THRESHOLD = settings.MONO_THRESHOLD
    LIGHT_DARK_RATIO = settings.LIGHT_DARK_RATIO

    MAX_SIGNALS = 128

    def __init__(self):
        # For identifying activity by absence of long silences.
        self._last_signals = collections.deque(maxlen=self.MAX_SIGNALS)

    def add_image(self, image, delta):
        """Add or discard new capture for analysing."""
        # Convert to monochrome.
        mono_func = lambda pixel: pixel > self.MONO_THRESHOLD and 255
        image = image.convert(mode=self.BW_MODE).point(
            mono_func, mode=self.MONO_MODE)

        # Decide if there's light or dark.
        hist = image.histogram()
        blacks = hist[0]
        if blacks:
            light_dark = float(hist[-1]) / blacks
            signal = light_dark > self.LIGHT_DARK_RATIO
        else:
            signal = True

        print(signal, delta)
