import warnings

from phue import Bridge

import settings
from sun import Sun


class Hue(object):
    """
    Classs to control Hue lights. Provides methods to trigger lights with full brightness
    when user arrives home and turn off all lights when all users have left home
    """
    def __init__(self):
        self.bridge = Bridge(settings.BRIDGE_IP)
        self.bridge.connect()
        self.sunset = Sun()
        print("Connected to Hue bridge!")

    def set_arrive(self):
        """
        Set all given lights to full brightes. If sun has set, trigger additional light
        settings.
        """
        for light in settings.ARRIVE_LIGHTS:
            self.bridge.set_light(light, 'on', True)
            self.bridge.set_light(light, 'bri', 255)
        if self.sunset.is_past_sunset():
            self.set_arrive_after_sunset()

    def set_arrive_after_sunset(self):
        warnings.warn("Set arrive after sunset is not implemented")
        pass

    def set_leave_home(self):
        """ Turn off all lights """
        for light in self.bridge.lights:
            light.on = False
