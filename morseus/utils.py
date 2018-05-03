"""Morseus common utilities that may be subject to the entire project."""


from kivy.app import App

from morseus import settings


get_app = lambda: App.get_running_app()

get_root = lambda: get_app().root


def calc_morse_fps():
    """Returns camera capturing desired frame rate."""
    fps = settings.SECOND / settings.UNIT
    # Tweak the amount in order to be more permissive with the fluctuations.
    return min(int(settings.FPS_FACTOR * fps), settings.MAX_FPS)


def dim_transform(first, second, transform):
    """Adapt `transform` dimensions following `first` to `second` rules."""
    # Compute aspect ratios.
    first_ratio, second_ratio = map(lambda pair: pair[0] / pair[1],
                                    [first, second])
    # Decide which from width/height fits and where is void left.
    diff = first_ratio - second_ratio
    fit = 0 if diff >= 0 else 1
    void = int(not fit)
    # Compute the co-ratio between two fits.
    coratio = first[fit] / second[fit]
    # Apply factors to current dimensions.
    adapt = lambda ent: map(lambda dim: ent[dim] / coratio, [0, 1])
    pos, size = map(adapt, transform)
    # Also compute and apply position correction.
    poscor = [0, 0]
    poscor[void] = (second[void] - first[void] / coratio) / 2
    pos = map(sum, zip(pos, poscor))
    # Return newly computed position and size.
    return pos, size
