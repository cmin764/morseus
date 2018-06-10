"""Natural User Interface for the Morseus app."""


import itertools
import threading
import time

from PIL import Image
from kivy.clock import Clock
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    ListProperty,
    NumericProperty,
    StringProperty,
)
from kivy.uix.tabbedpanel import TabbedPanelItem

from morseus import process, settings, utils
from morseus.settings import LOGGING


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
    START = "Start"
    STOP = "Stop"
    SEND_TOGGLE = {
        START: STOP,
        STOP: START,
    }

    output_text = StringProperty()
    input_text = StringProperty()
    transmitter_color = ColorProperty([0] * 3)
    send_button_text = StringProperty(START)
    camera_box_value = NumericProperty()
    adaptive_state = BooleanProperty()
    debug_state = BooleanProperty()

    def __init__(self, *args, **kwargs):
        super(MorseusLayout, self).__init__(*args, **kwargs)

        self.camera_box_value = int(settings.AREA.RATIO * 100)
        self.debug_state = LOGGING.DEBUG

        self._decoder = process.Decoder(self.debug_state)
        self._send_thread = None
        self._send_stop_tevent = threading.Event()

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
        self._decoder = process.Decoder(self.debug_state)
        # And finally clear received text so far.
        self.output_text = ""
        # Now turn on back the camera.
        camera.play = True

    def _display_signal(self, state):
        """Turn on/off the transmitter (according to `state`) and keep it like
        that until a next signal arrives.
        """
        value = int(state)
        self.transmitter_color = [value] * 3

    def _send_text(self):
        """Function which runs in a separate thread for text sending."""
        # Create a new alphabet translator and begin to obtain and show light
        # signals until the end of transmission.
        signal_func = (lambda state: Clock.schedule_once(
            lambda *_: self._display_signal(state)))
        _encoder = process.Encoder(
            self.input_text,
            signal_func,
            self._send_stop_tevent,
            self._decoder,
            self.debug_state,
            self.adaptive_state
        )
        _encoder.start()
        # The encoder just finished the job on its own or by being stopped.
        self.send_button_text = self.START

    def _start_sending(self):
        # Start the continuous sending process into a new thread.
        self._send_stop_tevent.clear()
        self._send_thread = threading.Thread(target=self._send_text)
        self._send_thread.start()

    def stop_sending(self):
        # Tell the sending process to stop and wait for it.
        self._send_stop_tevent.set()
        if self._send_thread:
            self._send_thread.join()

    def toggle_send_button(self):
        """Action triggered by the Start/Stop button for text sending."""
        txt = self.send_button_text
        if txt == self.START:
            self._start_sending()
        else:
            self.stop_sending()
        self.send_button_text = self.SEND_TOGGLE[txt]


class MorseusCamera(Camera, WidgetMixin):

    """Define custom camera actions and settings."""

    _AREA = settings.AREA
    CENTER_RATIO = _AREA.RATIO
    CENTER_WIDTH = _AREA.WIDTH

    # Focus rectangle dimensions.
    center_pos = ListProperty([0, 0])
    center_size = ListProperty([0, 0])
    # Focus rectangle update status.
    center_updated = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        super(MorseusCamera, self).__init__(*args, **kwargs)
        self._capture_event = None
        self._center_region = None
        self._center_metrics = None
        self._last_time = None

    def get_center_metrics(self, size, cache=True):
        """Returns a centered rectangular sub-shape of the given `size`."""
        if not (self._center_metrics and cache):
            # Normalize size, then compute aspect ratio and center of the image.
            width, height = map(float, size)
            aspect_ratio = width / height
            center = width / 2, height / 2

            # Now compute the centered smaller sub-area.
            box_ratio = self.root.camera_box_value / 100.0
            subwidth = width * box_ratio
            subwidth = max(subwidth, self.CENTER_WIDTH.MIN)
            subwidth = min(subwidth, self.CENTER_WIDTH.MAX)
            subsize = (subwidth, subwidth / aspect_ratio)

            # And finally the bottom-left origin point.
            subpoint = map(lambda pos, length: pos - length / 2,
                           center, subsize)

            self._center_metrics = (subpoint, subsize)
            self.center_updated = True

        return self._center_metrics

    def capture(self, delta, *_):
        """Capture the current screen and further process the image."""
        if not self.play:
            self._last_time = None
            return

        if not self._center_region or self.center_updated:
            tex = self.texture
            point, size = self.get_center_metrics(tex.size)
            region_args = itertools.chain(point, size)
            self._center_region = tex.get_region(*region_args)
            self.center_updated = False    # not updated anymore

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

    def update_center(self, cache=True):
        """Update the visual center focus area for feedback."""
        if not all(self.texture_size):
            # Texture not initialized yet.
            return

        # Get focus coordinates.
        point, size = self.get_center_metrics(self.texture_size, cache=cache)
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
