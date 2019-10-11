#!/usr/bin/env python3

from src.hue import Hue
from src.network import Network
from src.utils import setup_logger


if __name__ == "__main__":
    setup_logger()
    hue = Hue()
    network = Network(callback_leave=hue.set_leave_home, callback_join=hue.set_arrive)
