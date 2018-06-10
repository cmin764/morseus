"""Patch library bad behavior."""


import libmorse
from kivy import utils as kivy_utils
from kivy.clock import Clock
from kivy.core import camera as core_camera, core_select_lib
from kivy.uix import camera as uix_camera

from morseus import settings


CAM = settings.CAMERA_PROVIDERS
LOG = settings.LOGGING
PLATFORM = kivy_utils.platform


def patch_camera(set_provider=CAM.EXPLICIT):
    """Choose a predefined camera provider for some platforms."""
    CoreCamera = core_camera.Camera
    set_provider = set_provider or CAM.IMPLICIT.get(PLATFORM)

    if CAM.ENABLE and set_provider:
        for provider in core_camera.providers:
            if set_provider == provider[0]:
                core_camera.providers = (provider,)
                _CoreCamera = core_select_lib("camera", core_camera.providers)
                CoreCamera = _CoreCamera or CoreCamera
                break

    class PatchedCoreCamera(CoreCamera):

        def start(self, *args, **kwargs):
            ret = super(PatchedCoreCamera, self).start(*args, **kwargs)

            attrs = map(lambda attr: getattr(self, attr, None),
                        ["_update_ev", "fps"])
            if all(attrs) and self.fps > 1.0:
                self._update_ev.cancel()
                self._update_ev = Clock.schedule_interval(
                    self._update, 1.0 / self.fps
                )

            return ret

    core_camera.Camera = PatchedCoreCamera
    uix_camera.CoreCamera = core_camera.Camera


def patch_libmorse(logfile=LOG.FILE.EXPLICIT):
    if logfile is None:
        logfile = LOG.FILE.IMPLICIT.get(PLATFORM)
    # Do not take into account `True` or `None`.
    if logfile is False:
        # We deliberately do not want to log into files.
        libmorse.settings.LOGFILE = None


def patch_all(camera=True, libmorse=True):
    if camera:
        patch_camera()
    if libmorse:
        patch_libmorse()
