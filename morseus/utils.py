"""Morseus common utilities that may be subject to the entire project."""


from kivy.app import App

from morseus import settings


get_app = lambda: App.get_running_app()

get_root = lambda: get_app().root


def calc_morse_fps():
    """Returns camera capturing desired frame rate."""
    fps = settings.SECOND / settings.UNIT
    # Double the amount in order to be more permissive with the fluctuations.
    return int(2 * fps)
