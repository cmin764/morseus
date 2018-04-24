from kivy.app import App

from morseus.nui import Morseus


class MorseusApp(App):

    def build(self):
        return Morseus()


if __name__ == "__main__":
    MorseusApp().run()
