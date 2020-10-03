[![Build Status](https://travis-ci.com/vaahtokarkki/hue-geofencing.svg?token=xtdNg3EhGgxQjprnxrFy&branch=master)](https://travis-ci.com/vaahtokarkki/hue-geofencing) [![Maintainability](https://api.codeclimate.com/v1/badges/3f55e42840cda2ea959b/maintainability)](https://codeclimate.com/github/vaahtokarkki/hue-geofencing/maintainability) [![codecov](https://codecov.io/gh/vaahtokarkki/hue-geofencing/branch/master/graph/badge.svg)](https://codecov.io/gh/vaahtokarkki/hue-geofencing) [![Docker hub](https://img.shields.io/badge/Docker-Hub-blue)](https://hub.docker.com/r/vaahtokarkki/hue-geofencing/tags)


# Hue geofencing

Multi-user geofencing for Phillips Hue. No need to install additional software, geofencing is based on detecting devices online in the local network.

## Usage

Just add MAC-addresses of traced devices and the name of the light(s), which will turn on when the resident arrives home. After all devices have disconnected from the network, turn off all lights. In the future, turn on also additional lights/scene when arriving home after sunset.

## Requirements

* Python 3.6 or greater
* [tcdump](https://www.tcpdump.org/)
* [bluez](http://www.bluez.org/), if Bluetooth is enabled

## Setup

### Simple setup for Raspberry Pi Zero

Create `.env` file based on [.env.example](https://github.com/vaahtokarkki/hue-geofencing/blob/master/.env.example).

#### Enviroment variables

Set on `.env` ip-address of Hue bridge, names of lights that turn on when arriving home, and devices which to track. Multiple values can be inserted to `DEVICES` and `ARRIVE_LIGHTS`, separated by `,`.

Additional configuration:
* `EXCLUDE_LIGHTS`, lights to exclude when turning of all lights
* `BLUETOOTH_DEVICES`, Bluetooth mac address for given devices in format `wifi-mac;bt-mac` separated by `,`
* `LOCATION_LAT` and `LOCATION_LON`, required for getting sunset.
* `LOG_LEVEL`, Python logger level, default `INFO`
* `NETWORK_MASK`, network mask to scan initially when starting server
* `SCAN_INTERVAL`, how often to ping devices currently at home
* `DISABLE_START` and `DISABLE_END`, range in hours when home arrive action should be disabled

### Run with Docker Compose

```
$ git clone https://github.com/vaahtokarkki/hue-geofencing
$ cd hue-geofencing
$ docker-compose run armv6
```

Available environments on Docker are: `amd64`, `armv6` (for RPi Zero and RPi 1), `armv7`.

Docker images can be found on [Docker Hub](https://hub.docker.com/repository/docker/vaahtokarkki/hue-geofencing)

For best IoT-experience run Docker with [Watchtower](https://github.com/containrrr/watchtower) for automatic updates.

### Setup for other platforms
Server can be run also with python.

```bash
$ git clone https://github.com/vaahtokarkki/hue-geofencing
$ cd hue-geofencing
$ python -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ cp .env.example .env
```

Add required values to `.env`, see [instructions](#enviroment-variables) above.

Start server by
```
$ sudo python main.py
```
Note: sudo access is required for listening network.

## How it works

### Detecting home leave

Server keeps track of online devices and scans devices online periodically by pinging them.

Pinging a device is done with ARP-, ICMP- and TCP-ping. If device is not responding to any of those, ping with Bluetooth (l2ping), if Bluetooth MAC-address is provided.

If device is not responding after given times, assume it has left the house and remove it from list of devices online. After list is empty, turn off all lights as all residents have left the house.

### Detecting home arrive

Home arrive can be detected by listening packets on network (Wifi). If packet source is from tracked device and it is not on the list of online devices, assume that device has recently arrived home. Turn on given lights and add device to the list to prevent triggering home arrive multiple times for the same device.

After all residents are home, disable network listening and resume packet listening when someone leaves the house.

**Note: For more reliability use official Hue app own location aware features to trigger home coming, as device may not connect immediately to wifi.**

All network monitoring operations are made with [scapy](https://github.com/secdev/scapy).

### Sunset times

Server updates sunset and sunrise times once in a day. Home location is needed for getting correct sunset times. Data if fetched from open [Sunset Sunrise API](https://sunrise-sunset.org/api).

## Built with
* [scapy](https://github.com/secdev/scapy) - Network monitoring
* [phue](https://github.com/studioimaginaire/phue) - Hue light controls
* [schedule](https://github.com/dbader/schedule) - Schedule tasks
* [requests](https://2.python-requests.org/en/master/) - HTTP client

## Roadmap
* Add tests for `network.py`, probably needs lots of mocking.
* Get rid of subproces on Bluetooth ping and replace l2ping with some library providing same functionality
* Add Dokcer images for other platforms
