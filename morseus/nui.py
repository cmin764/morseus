"""Natural User Interface for the Morseus app."""


import itertools

from kivy.clock import Clock
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout

from morseus import settings, utils


class MorseusCamera(Camera):

    """Define custom camera actions and settings."""

    MORSE_FPS = utils.calc_morse_fps()

    _AREA = settings.AREA
    CENTER_RATIO = _AREA.RATIO
    CENTER_WIDTH = _AREA.WIDTH

    def __init__(self, *args, **kwargs):
        super(MorseusCamera, self).__init__(*args, **kwargs)
        self._capture_event = None

    @classmethod
    def get_center_metrics(cls, size):
        """Returns a centered rectangular sub-shape of the given `size`."""
        # Normalize size, then compute aspect ratio and center of the image.
        width, height = map(float, size)
        aspect_ratio = width / height
        center = width / 2, height / 2

        # Now compute the centered smaller sub-area.
        subwidth = width * cls.CENTER_RATIO
        subwidth = max(subwidth, cls.CENTER_WIDTH.MIN)
        subwidth = min(subwidth, cls.CENTER_WIDTH.MAX)
        subsize = (subwidth, subwidth / aspect_ratio)

        # And finally the bottom-left origin point.
        subpoint = map(lambda pos, length: pos - length / 2,
                       center, subsize)

        return subpoint, subsize

    def capture(self, *_):
        """Capture the current screen and further process the image."""
        tex = self.texture
        point, size = self.get_center_metrics(tex.size)
        region_args = itertools.chain(point, size)
        region = tex.get_region(*region_args)
        print(region)

    def on_texture(self, *args, **kwargs):
        """Callback for texture loading (usually happens once)."""
        ret = super(MorseusCamera, self).on_texture(*args, **kwargs)

        if not self._capture_event:
            period = 1.0 / self.MORSE_FPS
            self._capture_event = Clock.schedule_interval(
                self.capture, period)

        return ret


class Morseus(GridLayout):

    """Morseus root widget holding the entire NUI."""
