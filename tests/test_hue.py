from unittest.mock import Mock, patch

import pytest

from hue import Hue


@pytest.fixture
@patch('hue.Bridge')
@patch('sun.threading')
def hue(bridge, monkeypatch):
    return Hue()


def test_hue_constructor(hue):
    hue.bridge.connect.assert_called_once()


@patch('hue.Sun')
def test_hue_arrive_after_sunset(sun, hue):
    sun.is_past_sunset.return_value = True

    hue.set_arrive()
    for light in ["Light 1", "Light 2"]:
        hue.bridge.set_light.assert_any_call(light, 'on', True)
        hue.bridge.set_light.assert_any_call(light, 'bri', 255)
    sun.is_past_sunset.assert_called_once
    # TODO: assert after sunset light/scene call


@patch('hue.Sun')
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
