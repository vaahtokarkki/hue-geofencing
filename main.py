#!/usr/bin/env python3
from hue import Hue
from network import Network
import logging


if __name__ == "__main__":
    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    logger.info('creating an instance of auxiliary_module.Auxiliary')
    hue = Hue()
    network = Network(callback_leave=hue.set_leave_home, callback_join=hue.set_arrive)
