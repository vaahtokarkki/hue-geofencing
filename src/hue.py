import logging
import os
import time
from datetime import datetime, timedelta

from phue import Bridge
from pytz import timezone

from src.settings import (AFTER_SUNSET_SCENE, ARRIVE_LIGHTS, BRIDGE_IP,
                          DISABLE_END, DISABLE_START, EXCLUDE_LIGHTS)
from src.sun import Sun

log = logging.getLogger("main")


class Hue(object):
    """
    Class to control Hue lights. Provides methods to trigger lights with full brightness
    when user arrives home and turn off all lights when all users have left home
    """
    def __init__(self):
        config_path = f"{os.getcwd()}/.phue_config"
        try:
            self.bridge = Bridge(BRIDGE_IP, config_file_path=config_path)
        except OSError:
            log.error(f'Failed to connect to Hue bridge using address {BRIDGE_IP}')
            exit()
        self.__try_to_run(self.bridge.connect, [])
        bridge_name = self.__try_to_get(self.bridge.name, sleep=0.1)  # Test connection
        if not bridge_name:
            log.error(f'Failed to connect to Hue bridge using address {BRIDGE_IP}')
            exit()

        log.info(f'Connected to Hue bridge, {bridge_name}!')
        self.sunset = Sun()

    def set_arrive(self):
        """
        Set all given lights to full brightness. If sun has set, trigger additional light
        settings.
        """
        if self._is_disabled_time():
            log.info("Home arrive not triggered due disabled time")
            return

        for light in ARRIVE_LIGHTS():
            self.__try_to_run(self._turn_on_light, [light])
        if self.sunset.is_past_sunset():
            self.set_arrive_after_sunset()

    def set_arrive_after_sunset(self):
        self.activate_scene(AFTER_SUNSET_SCENE)

    def set_leave_home(self):
        """ Turn off all lights """
        all_lights = self.__try_to_get(self.bridge.lights)
        if not all_lights:
            return False

        for light in all_lights:
            if self.__try_to_get(light.name) in EXCLUDE_LIGHTS():
                continue
            self.__try_to_run(self._turn_off_light, [light.light_id])
        return True

    def activate_scene(self, name):
        """ Activate scene by name """
        scene = self.__try_to_run(self._resolve_scene, [name])
        if not scene or not self._is_scene_lights_off(scene):
            return
        return self.__try_to_run(self.bridge.activate_scene,
                                 [scene.group, scene.scene_id])

    def _is_scene_lights_off(self, scene):
        """
        Return True if any of lights in given scene is turned on
        """
        if not scene or not scene.lights:
            return False

        scene_lights = self.__try_to_run(self._get_lights, [scene.lights])
        if not scene_lights:
            return False
        return all(light.on is False for light in scene_lights)

    def _get_lights(self, lights):
        return [light for light in self.bridge.lights if light.light_id in lights]

    def _resolve_scene(self, name):
        """
        Resolve scene and group ids from scene name.
        Returns scene or None if scene not found
        """
        all_scenes = self.__try_to_get(self.bridge.scenes)
        if not all_scenes:
            return None
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
        self.bridge.set_light(light, 'on', False)
        return True

    def _turn_on_light(self, light):
        self.bridge.set_light(light, 'on', True)
        self.bridge.set_light(light, 'bri', 255)
        return True

    def _is_disabled_time(self):
        if not DISABLE_START or not DISABLE_END:
            return False

        tz = timezone("Europe/Helsinki")
        now = datetime.now(tz)
        start = now.replace(hour=DISABLE_START, minute=0, second=0, microsecond=0)
        end = now.replace(hour=DISABLE_END, minute=0, second=0, microsecond=0)
        if now.hour < DISABLE_START:
            start -= timedelta(days=1)
        if now.hour > DISABLE_START:
            end += timedelta(days=1)

        return now >= start and now <= end

    def __try_to_run(self, func, args, exceptions=(OSError,), amount=10, sleep=2):
        """ Try to run given function and catch given exceptions """
        for _ in range(amount):
            try:
                return func(*args)
            except exceptions as e:
                log.debug(f'Try to run failed, sleeping {sleep}s, {e}')
                time.sleep(sleep)
        log.info(f'Failed to run {func.__name__} with args {args}')
        return None

    def __try_to_get(self, property, exceptions=(OSError,), amount=10, sleep=2):
        for _ in range(amount):
            try:
                return property
            except exceptions as e:
                log.debug(f'Try to get failed, sleeping {sleep}s, {e}')
                time.sleep(sleep)
        log.info('Failed to get property')
        return None
