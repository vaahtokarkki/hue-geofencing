import threading
from datetime import date, datetime, timedelta
import time
import requests
import schedule

import settings


class Sun(object):
    """
    Class representing sunset time for given location. Provides sunset time and
    timestamp as datetime objects.
    When class is created, set up scheduler to update sunset and sunrise times at 12:00
    every day.

    Note: All times are in UTC
    """

    def __init__(self):
        self.update()
        schedule.every().day.at("12:00").do(self.update)
        self._scheduler = threading.Thread(target=self._run_schedule)
        self._scheduler.start()

    def update(self):
        """
        Update sunset and timestamp class variables. Returns True if sunset udpated
        successfully othervise False
        """
        data = self._get_sunset_sunrise()
        if not data:
            return False

        self.sunset = data[0]
        self.sunrise = data[1]
        self.timestamp = datetime.utcnow()
        return True

    def is_past_sunset(self):
        """
        Return True if sun is set, after sunset return True until sunrise
        """
        if not self.sunset or not self.sunrise:
            return False
        return self.sunset < datetime.utcnow() < self.sunrise

    def _run_schedule(self):
        """
        Start loop for scheduler. This should be run at own thread to prevent blocking
        """

        while True:
            schedule.run_pending()
            time.sleep(60)

    def _get_sunset_sunrise(self):
        """
        Return sunset and sunrise as datetime obejct in tuple or False if sunset
        time fetch failed. Sun time is fetched from external api and requires to
        location to be defined and valid in settings.

        Output: (sunset, sunrise)
        """

        location = settings.LOCATION
        if not location:
            return False

        resp = requests.get(
            f"https://api.sunrise-sunset.org/json?lat={location[0]}&lng={location[1]}"
        )

        if resp.status_code == 200:
            data = resp.json()
            sunset = self._parse_date(data["results"]["sunset"])
            sunrise = self._parse_date(data["results"]["sunrise"], next_day=True)
            return (sunset, sunrise)

        return False

    def _parse_date(self, input_time, next_day=False):
        """
        Return parsed datetime object from string or False if parse failed. If next_day is
        True add one day (tomorrow) to output.
        Input must in format "1:23:45 PM"
        """

        today = date.today()
        if next_day:
            today += timedelta(days=1)

        try:
            parsed = datetime.strptime(input_time, '%I:%M:%S %p')
            parsed = parsed.replace(year=today.year, month=today.month, day=today.day)
        except ValueError:
            return False
        return parsed
