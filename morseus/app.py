"""Morseus application controller."""


from kivy.app import App

from morseus import settings
from morseus.nui import MorseusLayout


class Morseus(App):

    def build(self):
        self.icon = settings.ICON
        return MorseusLayout()

    def on_stop(self):
        # Stop sending Morse signals in case we're doing that.
        self.root.stop_sending()
