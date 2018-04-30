"""Natural User Interface for the Morseus app."""


from kivy.clock import Clock
from kivy.uix.camera import Camera
from kivy.uix.gridlayout import GridLayout

from morseus import utils


class MorseusCamera(Camera):

    """Define custom camera actions and settings."""

    MORSE_FPS = utils.calc_morse_fps()

    def capture(self, delta, *_):
        """Capture the current screen and further process the image."""
        print(delta)

    def on_texture(self, *args, **kwargs):
        """Callback for texture loading (usually happens once)."""
        ret = super(MorseusCamera, self).on_texture(*args, **kwargs)

        Clock.schedule_interval(self.capture, 1.0 / self.MORSE_FPS)

        return ret


class Morseus(GridLayout):

    """Morseus root widget holding the entire NUI."""
