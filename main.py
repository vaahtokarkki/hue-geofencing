#!/usr/bin/env python3
import logging

import settings
from hue import Hue
from network import Network


if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.setLevel(settings.LOG_LEVEL)
    logger.addHandler(logging.StreamHandler())
    logger.info('creating an instance of auxiliary_module.Auxiliary')
    hue = Hue()
    network = Network(callback_leave=hue.set_leave_home, callback_join=hue.set_arrive)
