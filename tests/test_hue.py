from unittest.mock import Mock, patch

import pytest

from hue import Hue


@pytest.fixture
def mock(mocker):
    mock = mocker.Mock()
    mocker.patch('hue.settings', mock)
    mocker.patch('hue.Sun', mock)

    mock.BRIDGE_IP = "192.168.1.0"
    mock.ARRIVE_LIGHTS = ["Light 1", "Light 2"]

    mock.is_past_sunset.return_value = "Moi"

    return mock


@pytest.fixture
@patch('hue.Bridge')
def hue(bridge, mock):
    return Hue()


def test_hue_constructor(mock, hue):
    hue.bridge.connect.assert_called_once()


@patch('hue.Sun')
def test_hue_arrive_after_sunset(sun, mock, hue):
    sun.is_past_sunset.return_value = True

    hue.set_arrive()
    for light in ["Light 1", "Light 2"]:
        hue.bridge.set_light.assert_any_call(light, 'on', True)
        hue.bridge.set_light.assert_any_call(light, 'bri', 255)
    hue.sunset.is_past_sunset.assert_called_once
    # TODO: assert after sunset light/scene call


def test_hue_arrive_beofire_sunset(mock, hue):

    hue.set_arrive()
    for light in ["Light 1", "Light 2"]:
        hue.bridge.set_light.assert_any_call(light, 'on', True)
        hue.bridge.set_light.assert_any_call(light, 'bri', 255)
    hue.sunset.is_past_sunset.assert_called_once


def test_hue_leave(mock, hue):
    hue.bridge.lights = [Mock(), Mock()]
    hue.set_leave_home()
    for light in hue.bridge.lights:
        assert not light.on
