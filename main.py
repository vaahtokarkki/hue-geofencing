#!/usr/bin/env python3

from src.hue import Hue
from src.network import Network
from src.utils import setup_logger


def version():
    import logging
    logger = logging.getLogger("main")
    logger.info(f'Hue geofencing version {open("VERSION", "r").read()}')


if __name__ == "__main__":
    setup_logger()
    version()
    hue = Hue()
    network = Network(callback_leave=hue.set_leave_home, callback_join=hue.set_arrive)
