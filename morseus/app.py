"""Morseus application controller."""


from kivy.app import App

from morseus.nui import MorseusLayout


class Morseus(App):

    def build(self):
        return MorseusLayout()
