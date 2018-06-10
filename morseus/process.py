"""Process images into timed Morse signals."""


import collections
import operator
import threading
import time
from Queue import Queue

import libmorse
import numpy
from PIL import ImageFilter

from morseus import settings
from morseus.settings import LOGGING


class Decoder(object):

    """Interpret black & white images as Morse code."""

    BW_MODE = "L"
    MONO_MODE = "1"
    MONO_THRESHOLD = settings.MONO_THRESHOLD
    LIGHT_DARK_RATIO = settings.LIGHT_DARK_RATIO

    MAX_SIGNALS = 128

    def __init__(self, debug):
        """Instantiate `Decoder` object with the arguments below.

        :param bool debug: show debug messages or not
        """
        # For identifying activity by absence of long silences.
        self._last_signals = collections.deque(maxlen=self.MAX_SIGNALS)
        # Last created thread (waiting purposes).
        self._last_thread = None
        # Morse translator.
        self._translate = libmorse.translate_morse(
            use_logging=LOGGING.USE, debug=debug)
        # Initialize translator coroutine.
        self._translator = self._translate.next()[0]
        self._translate_lock = threading.Lock()
        # Output queue of string letters.
        self._letters_queue = Queue()

    @staticmethod
    def _flood_fill(image, node, seen):
        """Find white spots and return their area."""
        queue = collections.deque()
        area = 0

        def add_pos(pos):
            # Check position and retrieve pixel.
            width, height = image.size
            valid = 0 <= pos[0] < width and 0 <= pos[1] < height
            if not valid:
                return False
            pixel = image.getpixel(pos)
            lin, col = pos
            if not pixel or seen[lin, col]:
                return False
            # White pixel detected.
            queue.append(pos)
            seen[lin, col] = True
            return True

        area += add_pos(node)
        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        while queue:
            node = queue.pop()
            for move in moves:
                adj = tuple(map(sum, zip(node, move)))
                area += add_pos(adj)

        return area

    @classmethod
    def _examine_circles(cls, image, img_area):
        """Check if we have the usual spot & noise pattern."""
        areas = []
        width, height = image.size
        # Generate the visiting matrix.
        seen = numpy.zeros((width, height))
        # Take each white not visited pixel and identify spot from it.
        for xpix in range(width):
            for ypix in range(height):
                pixel = image.getpixel((xpix, ypix))
                if not pixel or seen[xpix, ypix]:
                    continue
                # We've got a non-visited white pixel.
                area = cls._flood_fill(image, (xpix, ypix), seen)
                areas.append(area)
        if not areas:
            # No spots detected.
            return False

        # Now compare all the areas in order to check the pattern.
        main_area = max(areas)
        areas.remove(main_area)
        noise = True    # rest of the spots are just noise
        for area in areas:
            ratio = float(area) / main_area
            if ratio > settings.SPOT_NOISE_RATIO:
                # Not noise anymore.
                noise = False
                break

        # If we remain with the `noise`, then we have a recognized pattern.
        # Also check if the spot isn't too tiny.
        ratio = float(main_area) / img_area
        return noise and ratio > settings.SPOT_MIN_RATIO

    def _add_image(self, image, delta, last_thread):
        """Add or discard new capture for analysing."""
        # Convert to black & white, then apply blur.
        image = image.convert(mode=self.BW_MODE).filter(ImageFilter.BLUR)
        # Convert to monochrome.
        mono_func = lambda pixel: pixel > self.MONO_THRESHOLD and 255
        image = image.point(mono_func, mode=self.MONO_MODE)
        # Get image area and try to crop the extra space.
        img_area = operator.mul(*image.size)
        if settings.BOUNDING_BOX:
            # Crop unnecessary void around the light object.
            box = image.getbbox()
            if box:
                # Check if the new area isn't too small comparing to the
                # original.
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
            if not signal and light_dark:
                signal = self._examine_circles(image, img_area)
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

    def get_learnt_metrics(self):
        """Returns learnt translator `unit` and `config`."""
        trans = self._translator
        return trans.unit, trans.config

    def close(self):
        """Close the translator and free resources."""
        # Wait for the last started thread to finish (and all before it).
        if self._last_thread:
            self._last_thread.join()
        self._translator.wait()
        self._translator.close()
        self._last_signals.clear()


class Encoder(object):

    """Encode text into Morse signals."""

    def __init__(self, text, signal_func, stop_event, decoder, debug,
                 adaptive):
        """Instantiate `Encoder` object with the mandatory arguments below.

        :param str text: text to be translated
        :param signal_func: function that is called for each new state of the
            signal display
        :param stop_event: threading event which signals when to stop the
            processing & interpretation
        :param decoder: Decoder object used to read latest learnt metrics
        :param bool debug: show debug messages or not
        :param bool adaptive: "talk" in the same way we "listened"
        """
        self._text = text
        self._signal_func = signal_func
        self._stop_event = stop_event
        self._decoder = decoder

        # Create translator object for encoding text into Morse code quanta.
        self._translator = libmorse.AlphabetTranslator(
            use_logging=LOGGING.USE, debug=debug)
        # Use learnt unit and ratios instead of the default hardcoded ones.
        if adaptive:
            unit, config = decoder.get_learnt_metrics()
            if unit:
                # Use it when we have a learnt `unit` only.
                self._translator.unit = unit
            # We're having ratios no matter what, because we start with a
            # predefined standard set (which should be followed by any
            # sender as closest as it can).
            self._translator.update_ratios(config)

    def start(self):
        """Starts the whole process as a blocking call until finish or
        stopped.
        """
        # Send and process all characters at once.
        items = list(self._text.upper())
        for item in items:
            self._translator.put(item)
        _, result = libmorse.get_translator_results(
            self._translator, force_wait=True
        )
        self._translator.close()

        # Now send these resulted signals according to their duration.
        for state, delta in result:
            self._signal_func(state)
            time.sleep(delta / settings.SECOND)
            if self._stop_event.is_set():
                break

        # Every time we're ending with a silence.
        self._signal_func(False)
