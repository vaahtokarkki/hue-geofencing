#!/usr/bin/env python3
import logging

import src.settings as settings
from src.hue import Hue
from src.network import Network

if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.setLevel(settings.LOG_LEVEL())
    logger.addHandler(logging.StreamHandler())
    hue = Hue()
    network = Network(callback_leave=hue.set_leave_home, callback_join=hue.set_arrive)
