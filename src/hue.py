import logging
import os
import time
from datetime import datetime, timedelta

from phue import Bridge

from src.settings import (AFTER_SUNSET_SCENE, ARRIVE_LIGHTS, BRIDGE_IP,
                          EXCLUDE_LIGHTS, DISABLE_END, DISABLE_START)
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
        print("lkjvlkfjg", self._is_disabled_time())
        if self._is_disabled_time():
            return

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
        if not scene or not self._scene_lights_off(scene):
            return
        self.bridge.activate_scene(scene.group, scene.scene_id)

    def _scene_lights_off(self, scene):
        """
        Return True if any of lights in given scene is turned on
        """
        if not scene or not scene.lights:
            return False

        scene_lights = self._get_lights(scene.lights)
        return all(light.on is False for light in scene_lights)

    def _get_lights(self, lights):
        return [light for light in self.bridge.lights if light.light_id in lights]

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

    def _is_disabled_time(self):
        if not DISABLE_START or not DISABLE_END:
            return False

        now = datetime.now()
        start = now.replace(hour=DISABLE_START, minute=0, second=0, microsecond=0)
        end = now.replace(hour=DISABLE_END, minute=0, second=0, microsecond=0)
        if now.hour < DISABLE_START:
            start -= timedelta(days=1)
        if now.hour > DISABLE_START:
            end += timedelta(days=1)

        return now > start and now < end
