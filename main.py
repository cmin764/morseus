#! /usr/bin/env python


from kivy.app import App

from morseus import Morseus


class MorseusApp(App):

    def build(self):
        return Morseus()


if __name__ == "__main__":
    MorseusApp().run()
