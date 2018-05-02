"""Process images into timed Morse signals."""


import collections
import threading
from Queue import Queue

import libmorse

from morseus import settings


class Decoder(object):

    """Interpret black & white images as Morse code."""

    BW_MODE = "L"
    MONO_MODE = "1"
    MONO_THRESHOLD = settings.MONO_THRESHOLD
    LIGHT_DARK_RATIO = settings.LIGHT_DARK_RATIO

    MAX_SIGNALS = 128

    def __init__(self):
        # For identifying activity by absence of long silences.
        self._last_signals = collections.deque(maxlen=self.MAX_SIGNALS)
        self._translate = libmorse.translate_morse()
        self._translate.next()    # initialize translator coroutine
        self._translate_lock = threading.Lock()
        self._letters_queue = Queue()

    def add_image(self, image, delta, last_thread):
        """Add or discard new capture for analysing."""
        # Convert to monochrome.
        mono_func = lambda pixel: pixel > self.MONO_THRESHOLD and 255
        image = image.convert(mode=self.BW_MODE).point(
            mono_func, mode=self.MONO_MODE)

        # Decide if there's light or dark.
        hist = image.histogram()
        blacks = hist[0]
        if blacks:
            light_dark = float(hist[-1]) / blacks
            signal = light_dark > self.LIGHT_DARK_RATIO
        else:
            signal = True

        item = (signal, delta * settings.SECOND)
        if last_thread:
            last_thread.join()
        with self._translate_lock:    # isn't necessary, but paranoia reasons
            letters = self._translate.send(item)[1]
            if letters:
                self._letters_queue.put(letters)
                self._letters_queue.task_done()

    def get_letters(self):
        """Retrieve all present letters in the queue as as string."""
        all_letters = []
        while not self._letters_queue.empty():
            letters = self._letters_queue.get()
            all_letters.extend(letters)
        return "".join(all_letters)
