from unittest.mock import Mock, patch

import pytest

from src.hue import Hue


@pytest.fixture
@patch('src.hue.Bridge')
@patch('src.sun.threading')
@patch('src.hue.Sun')
def hue(bridge, monkeypatch, sun):
    hue = Hue()
    scene = Mock()
    scene.name = "After sunset scene"
    scene.group = 1
    scene.scene_id = "scene_id"
    hue.bridge.scenes = [scene]
    return hue


def test_hue_constructor(hue):
    hue.bridge.connect.assert_called_once()


def test_hue_arrive_after_sunset(hue):
    hue.sunset.is_past_sunset.return_value = True
    hue.set_arrive()
    for light in ["Light 1", "Light 2"]:
        hue.bridge.set_light.assert_any_call(light, 'on', True)
        hue.bridge.set_light.assert_any_call(light, 'bri', 255)
    hue.sunset.is_past_sunset.assert_called_once
    hue.bridge.activate_scene.assert_called_once_with(1, "scene_id")


@patch('src.hue.Sun')
def test_hue_arrive_beofire_sunset(sun, hue):
    hue.set_arrive()
    for light in ["Light 1", "Light 2"]:
        hue.bridge.set_light.assert_any_call(light, 'on', True)
        hue.bridge.set_light.assert_any_call(light, 'bri', 255)
    sun.is_past_sunset.assert_called_once


def test_hue_leave(hue):
    hue.bridge.lights = [Mock(), Mock()]
    hue.set_leave_home()
    for light in hue.bridge.lights:
        assert not light.on
