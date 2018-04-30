"""Morseus common utilities that may be subject to the entire project."""


from morseus import settings


def calc_morse_fps():
    """Returns camera capturing desired frame rate."""
    fps = settings.SECOND / settings.UNIT
    # Double the amount in order to be more permissive with the fluctuations.
    return int(2 * fps)
