"""Natural User Interface for the Morseus app."""


import itertools
import threading

from PIL import Image
from kivy.clock import Clock
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivy.uix.tabbedpanel import TabbedPanelItem

from morseus import process, settings, utils


_MORSE_FPS = utils.calc_morse_fps()
MORSE_PERIOD = 1.0 / _MORSE_FPS


class WidgetMixin(object):

    """Gives access to the `app` and `root` objects."""

    def __init__(self, *args, **kwargs):
        super(WidgetMixin, self).__init__(*args, **kwargs)
        self._app = None
        self._root = None

    @property
    def app(self):
        if not self._app:
            self._app = utils.get_app()
        return self._app

    @property
    def root(self):
        if not self._root:
            self._root = utils.get_root()
        return self._root


class MorseusLayout(GridLayout):

    """Morseus root widget holding the entire NUI."""

    TEXTURE_MODE = "RGBA"

    output_text = StringProperty()

    def __init__(self, *args, **kwargs):
        super(MorseusLayout, self).__init__(*args, **kwargs)
        self._decoder = process.Decoder()
        self._last_thread = None

        Clock.schedule_interval(self._update_output_text, MORSE_PERIOD)

    def _update_output_text(self, *_):
        text = self._decoder.get_letters()
        self.output_text += text

    def add_region(self, region, delta):
        """Add new capture of interest to the analyser."""
        image = Image.frombytes(self.TEXTURE_MODE, region.size, region.pixels)
        thread = threading.Thread(
            target=self._decoder.add_image,
            args=(image, delta),
            kwargs={"last_thread": self._last_thread}
        )
        thread.start()
        self._last_thread = thread


class MorseusCamera(Camera, WidgetMixin):

    """Define custom camera actions and settings."""

    _AREA = settings.AREA
    CENTER_RATIO = _AREA.RATIO
    CENTER_WIDTH = _AREA.WIDTH

    def __init__(self, *args, **kwargs):
        super(MorseusCamera, self).__init__(*args, **kwargs)
        self._capture_event = None
        self._center_region = None

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

    def capture(self, delta, *_):
        """Capture the current screen and further process the image."""
        if not self.play:
            return

        if not self._center_region:
            tex = self.texture
            point, size = self.get_center_metrics(tex.size)
            region_args = itertools.chain(point, size)
            self._center_region = tex.get_region(*region_args)

        # Load and further process region as PIL image.
        self.root.add_region(self._center_region, delta)

    def on_texture(self, *args, **kwargs):
        """Callback for texture loading (usually happens once)."""
        ret = super(MorseusCamera, self).on_texture(*args, **kwargs)

        if not self._capture_event:
            self._capture_event = Clock.schedule_interval(
                self.capture, MORSE_PERIOD)

        return ret


class MorseusTab(TabbedPanelItem, WidgetMixin):

    """Custom notebook tabs."""

    def on_touch_down(self, touch, *args, **kwargs):
        if self.collide_point(*touch.pos):
            root = self.root
            play = self == root.ids.receive_tab
            root.ids.morseus_camera.play = play

        return super(MorseusTab, self).on_touch_down(touch, *args, **kwargs)
