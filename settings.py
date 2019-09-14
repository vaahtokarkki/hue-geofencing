import os

from dotenv import load
load()


def _get_devices():
    device_list = os.getenv("DEVICES", "")
    device_list = device_list.split(",")
    if not all(len(device) == 17 for device in device_list):
        raise ValueError("Invalid MAC address")
    return device_list


def _get_arrive_lights():
    return os.getenv("ARRIVE_LIGHTS", "").split(",")


def _get_location():
    lat = os.getenv("LOCATION_LAT")
    lon = os.getenv("LOCATION_LON")

    if not lat or not lon:
        return False

    try:
        location = (int(lat), int(lon))
    except (ValueError):
        return False
    return location


LOG_LEVEL = os.getenv("LOG_LEVEL", 20)
SCAN_INTERVAL = os.getenv("SCAN_INTERVAL", 300)
NETWORK_MASK = os.getenv("NETWORK_MASK", "192.168.1.0/24")
BRIDGE_IP = os.getenv("BRIDGE_IP")
DEVICES = _get_devices()
ARRIVE_LIGHTS = _get_arrive_lights()
LOCATION = _get_location()
