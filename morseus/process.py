"""Process images into timed Morse signals."""


import collections
import operator
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
        # Last created thread (waiting purposes).
        self._last_thread = None
        # Morse translator.
        self._translate = libmorse.translate_morse()
        # Initialize translator coroutine.
        self._translator = self._translate.next()[0]
        self._translate_lock = threading.Lock()
        # Output queue of string letters.
        self._letters_queue = Queue()

    def _add_image(self, image, delta, last_thread):
        """Add or discard new capture for analysing."""
        # Convert to monochrome.
        mono_func = lambda pixel: pixel > self.MONO_THRESHOLD and 255
        image = image.convert(mode=self.BW_MODE).point(
            mono_func, mode=self.MONO_MODE)
        if settings.BOUNDING_BOX:
            # Crop unnecessary void around the light object.
            box = image.getbbox()
            if box:
                # Check if the new area isn't too small comparing to the
                # original.
                img_area = operator.mul(*image.size)
                box_area = operator.mul(
                    *map(lambda pair: abs(box[pair[0]] - box[pair[1]]),
                         [(0, 2), (1, 3)])
                )
                if float(box_area) / img_area > settings.BOX_MIN_RATIO:
                    image = image.crop(box=box)

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
            self._translator, letters = self._translate.send(item)
            if letters:
                self._letters_queue.put(letters)
                self._letters_queue.task_done()

    def add_image(self, *args, **kwargs):
        """Threaded scaffold for adding images into processing."""
        kwargs["last_thread"] = self._last_thread
        thread = threading.Thread(
            target=self._add_image,
            args=args,
            kwargs=kwargs
        )
        thread.start()
        self._last_thread = thread

    def get_letters(self):
        """Retrieve all present letters in the queue as as string."""
        all_letters = []
        while not self._letters_queue.empty():
            letters = self._letters_queue.get()
            all_letters.extend(letters)
        return "".join(all_letters)

    def close(self):
        """Close the translator and free resources."""
        # Wait for the last started thread to finish (and all before it).
        if self._last_thread:
            self._last_thread.join()
        self._translator.wait()
        self._translator.close()
        self._last_signals.clear()
