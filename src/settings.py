import os

from dotenv import load

if not os.getenv("TEST_RUN", False):
    load()


def _get_devices():
    device_list = os.getenv("DEVICES", "")
    device_list = device_list.split(",")
    if not all(len(device) == 17 for device in device_list):
        raise ValueError("Invalid MAC address")
    return device_list


def _get_bluetooth_devices():
    device_list = os.getenv("BLUETOOTH_DEVICES", "")
    device_list = device_list.split(",")
    wifi_addresses = []
    bt_addresses = []
    for device in device_list:
        splitted = device.split(";")
        wifi_addresses.append(splitted[0])
        bt_addresses.append(splitted[1])

    return {wifi: bt for wifi, bt in zip(wifi_addresses, bt_addresses)}


def _get_arrive_lights():
    return os.getenv("ARRIVE_LIGHTS", "").split(",")


def _get_excluded_lights():
    return os.getenv("EXCLUDE_LIGHTS", "").split(",")


def _get_location():
    lat = os.getenv("LOCATION_LAT")
    lon = os.getenv("LOCATION_LON")

    if not lat or not lon:
        return False

    try:
        location = (int(float(lat)), int(float(lon)))
    except (ValueError):
        raise ValueError(f"Invalid location {lat}, {lon}")
    return location


def _get_log_level():
    level = os.getenv("LOG_LEVEL", 20)
    return int(level)


LOG_LEVEL = _get_log_level
SCAN_INTERVAL = os.getenv("SCAN_INTERVAL", 5)
DISABLE_START = os.getenv("DISABLE_START")  # Disable start hours
if DISABLE_START:
    DISABLE_START = int(DISABLE_START)
DISABLE_END = os.getenv("DISABLE_END")  # Disable end hours
if DISABLE_END:
    DISABLE_END = int(DISABLE_END)
NETWORK_MASK = os.getenv("NETWORK_MASK", "192.168.1.0/24")
BRIDGE_IP = os.getenv("BRIDGE_IP")
DEVICES = _get_devices
BLUETOOTH_DEVICES = _get_bluetooth_devices
ARRIVE_LIGHTS = _get_arrive_lights
EXCLUDE_LIGHTS = _get_excluded_lights
AFTER_SUNSET_SCENE = os.getenv("AFTER_SUNSET", None)
LOCATION = _get_location
PING_SCHEDULE = os.getenv('PING_SCHEDULE', False)
