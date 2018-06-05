"""Natural User Interface for the Morseus app."""


import itertools
import time

from PIL import Image
from kivy.clock import Clock
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.properties import (
    ListProperty,
    StringProperty,
)
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


class CapitalTextInput(TextInput):

    def insert_text(self, string, *args, **kwargs):
        return super(CapitalTextInput, self).insert_text(
            string.upper(), *args, **kwargs
        )


class MorseusLayout(GridLayout):

    """Morseus root widget holding the entire NUI."""

    TEXTURE_MODE = "RGBA"

    output_text = StringProperty()

    def __init__(self, *args, **kwargs):
        super(MorseusLayout, self).__init__(*args, **kwargs)
        self._decoder = process.Decoder()

        Clock.schedule_interval(self._update_output_text, MORSE_PERIOD)

    def _update_output_text(self, *_):
        text = self._decoder.get_letters()
        self.output_text += text

    def add_region(self, region, delta):
        """Add new capture of interest to the analyser."""
        image = Image.frombytes(self.TEXTURE_MODE, region.size, region.pixels)
        self._decoder.add_image(image, delta)

    def reset_receiver(self):
        """Renew the state of the receiver."""
        # First, stop the camera, in order to interrupt the feed.
        camera = self.ids.morseus_camera
        camera.play = False
        # Now signal the decoder to finish.
        self._decoder.close()
        # Recreate the decoding objects.
        self._decoder = process.Decoder()
        # And finally clear received text so far.
        self.output_text = ""
        # Now turn on back the camera.
        camera.play = True


class MorseusCamera(Camera, WidgetMixin):

    """Define custom camera actions and settings."""

    _AREA = settings.AREA
    CENTER_RATIO = _AREA.RATIO
    CENTER_WIDTH = _AREA.WIDTH

    # Focus rectangle dimensions.
    center_pos = ListProperty([0, 0])
    center_size = ListProperty([0, 0])

    def __init__(self, *args, **kwargs):
        super(MorseusCamera, self).__init__(*args, **kwargs)
        self._capture_event = None
        self._center_region = None
        self._center_metrics = None
        self._last_time = None

    def get_center_metrics(self, size):
        """Returns a centered rectangular sub-shape of the given `size`."""
        if not self._center_metrics:
            # Normalize size, then compute aspect ratio and center of the image.
            width, height = map(float, size)
            aspect_ratio = width / height
            center = width / 2, height / 2

            # Now compute the centered smaller sub-area.
            subwidth = width * self.CENTER_RATIO
            subwidth = max(subwidth, self.CENTER_WIDTH.MIN)
            subwidth = min(subwidth, self.CENTER_WIDTH.MAX)
            subsize = (subwidth, subwidth / aspect_ratio)

            # And finally the bottom-left origin point.
            subpoint = map(lambda pos, length: pos - length / 2,
                           center, subsize)

            self._center_metrics = (subpoint, subsize)

        return self._center_metrics

    def capture(self, delta, *_):
        """Capture the current screen and further process the image."""
        if not self.play:
            self._last_time = None
            return

        if not self._center_region:
            tex = self.texture
            point, size = self.get_center_metrics(tex.size)
            region_args = itertools.chain(point, size)
            self._center_region = tex.get_region(*region_args)

        # Load and further process region as PIL image.
        now = time.time()
        if settings.TIME_DELTA and self._last_time:
            delta = now - self._last_time
        self._last_time = now
        self.root.add_region(self._center_region, delta)

    def on_texture(self, *args, **kwargs):
        """Callback for texture loading (usually happens once)."""
        ret = super(MorseusCamera, self).on_texture(*args, **kwargs)

        # Start periodic capturing event.
        if not self._capture_event:
            self._capture_event = Clock.schedule_interval(
                self.capture, MORSE_PERIOD)

        # Mark the focus area for capturing.
        self.update_center()

        return ret

    def update_center(self):
        """Update the visual center focus area for feedback."""
        if not all(self.texture_size):
            # Texture not initialized yet.
            return

        # Get focus coordinates.
        point, size = self.get_center_metrics(self.texture_size)
        # Transform `point` and `size` from texture to widget proportions.
        point, size = utils.dim_transform(
            self.texture_size, self.size, (point, size))
        # Texture position is relative to its parent widget (Camera).
        abs_point = map(sum, zip(self.pos, point))
        self.center_pos = abs_point
        self.center_size = size


class MorseusTab(TabbedPanelItem, WidgetMixin):

    """Custom notebook tabs."""

    def on_touch_down(self, touch, *args, **kwargs):
        if self.collide_point(*touch.pos):
            root = self.root
            play = self == root.ids.receive_tab
            root.ids.morseus_camera.play = play

        return super(MorseusTab, self).on_touch_down(touch, *args, **kwargs)
