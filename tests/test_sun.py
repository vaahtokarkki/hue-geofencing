import pytest
from datetime import datetime, timedelta
from sun import Sun


@pytest.fixture
def mock(mocker):
    mock = mocker.Mock()
    mocker.patch('sun.requests', mock)
    mocker.patch('sun.threading.Thread', mock)

    mock.get.return_value.status_code = 200
    mock.get.return_value.json.return_value = {
        "results": {
            "sunrise": "3:15:00 AM",
            "sunset": "5:30:00 PM",
        }
    }

    return mock


def test_sun(mock):
    sun = Sun()
    sunrise = datetime.utcnow() + timedelta(days=1)
    sunrise = sunrise.replace(hour=3, minute=15, second=0, microsecond=0)
    sunset = datetime.utcnow().replace(hour=17, minute=30, second=0, microsecond=0)
    timestamp_delta = datetime.utcnow() - sun.timestamp

    assert sunrise == sun.sunrise
    assert sunset == sun.sunset
    assert round(timestamp_delta.total_seconds()) == 0
    assert sun._scheduler is not None
