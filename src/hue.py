import logging
import os
import time

from phue import Bridge

from src.settings import (AFTER_SUNSET_SCENE, ARRIVE_LIGHTS, BRIDGE_IP,
                          EXCLUDE_LIGHTS)
from src.sun import Sun

log = logging.getLogger("main")


class Hue(object):
    """
    Class to control Hue lights. Provides methods to trigger lights with full brightness
    when user arrives home and turn off all lights when all users have left home
    """
    def __init__(self):
        config_path = f"{os.getcwd()}/.phue_config"
        self.bridge = Bridge(BRIDGE_IP, config_file_path=config_path)
        self.bridge.connect()
        self.sunset = Sun()
        log.info("Connected to Hue bridge!")

    def set_arrive(self):
        """
        Set all given lights to full brightness. If sun has set, trigger additional light
        settings.
        """
        for light in ARRIVE_LIGHTS():
            self.bridge.set_light(light, 'on', True)
            self.bridge.set_light(light, 'bri', 255)
        if self.sunset.is_past_sunset():
            self.set_arrive_after_sunset()

    def set_arrive_after_sunset(self):
        self.activate_scene(AFTER_SUNSET_SCENE)

    def set_leave_home(self):
        """ Turn off all lights """
        for light in self.bridge.lights:
            if light.name in EXCLUDE_LIGHTS():
                continue
            self._turn_off_light(light)

    def activate_scene(self, name):
        """ Activate scene by name """
        scene = self._resolve_scene(name)
        if not scene or self._scene_lights_on(scene):
            return
        self.bridge.activate_scene(scene.group, scene.scene_id)

    def _scene_lights_on(self, scene):
        """
        Return True if any of lights in given scene is turned on
        """
        if not scene or not scene.lights:
            return False

        return not all(light.on is False for light in scene.lights)

    def _resolve_scene(self, name):
        """
        Resolve scene and group ids from scene name.
        Returns scene or None if scene not found
        """
        for scene in self.bridge.scenes:
            if scene.name == name:
                return scene
        return None

    def _turn_off_light(self, light):
        """
        Utility function to turn off given light and catch possible OSError.

        OSError gets raised sometimes witch coded 101 Network is unreachable. Try to turn
        off light given times again if exception is raised.

        Returns True if light is turned off successfully, otherwise False
        """
        for _ in range(10):
            try:
                light.on = False
                return True
            except OSError:
                time.sleep(0.5)

        log.debug(f"Failed to turn off light {light}")
        return False
