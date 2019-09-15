import pytest

from importlib import reload
import settings


def test_location(monkeypatch):
    monkeypatch.setenv("LOCATION_LAT", "66")
    monkeypatch.setenv("LOCATION_LON", "26")
    reload(settings)
    assert settings.LOCATION() == (66, 26)


def test_location_decimals(monkeypatch):
    monkeypatch.setenv("LOCATION_LAT", "55.123")
    monkeypatch.setenv("LOCATION_LON", "27.123")

    reload(settings)
    assert settings.LOCATION() == (55, 27)


def test_location_invalid(monkeypatch):
    monkeypatch.setenv("LOCATION_LAT", "lat")
    monkeypatch.setenv("LOCATION_LON", "lon")
    with pytest.raises(ValueError):
        reload(settings)
        settings.LOCATION()


def test_location_empty(monkeypatch):
    monkeypatch.delenv("LOCATION_LAT", raising=False)
    monkeypatch.delenv("LOCATION_LON", raising=False)
    reload(settings)
    assert not settings.LOCATION()


def test_devices(monkeypatch):
    monkeypatch.setenv("DEVICES", "00:1B:44:11:3A:B7,E8:FC:AF:B9:BE:A2")
    reload(settings)
    assert set(settings.DEVICES()) == {"00:1B:44:11:3A:B7", "E8:FC:AF:B9:BE:A2"}


def test_devices_empty(monkeypatch):
    monkeypatch.setenv("DEVICES", "")
    with pytest.raises(ValueError):
        reload(settings)
        settings.DEVICES()


def test_devices_invalid_value(monkeypatch):
    monkeypatch.setenv("DEVICES", "this is not a mac address")
    with pytest.raises(ValueError):
        reload(settings)
        settings.DEVICES()


def test_devices_missing(monkeypatch):
    monkeypatch.delenv("DEVICES", raising=False)
    with pytest.raises(ValueError):
        reload(settings)
        settings.DEVICES()
