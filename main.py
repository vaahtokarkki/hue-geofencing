#!/usr/bin/env python3

import time

import schedule
from guppy import hpy

from src.hue import Hue
from src.network import Network
from src.utils import setup_logger


def print_heap(h=None):
    print("Heap")
    print(h.heap())


if __name__ == "__main__":
    setup_logger()
    heap = hpy()
    hue = Hue()
    network = Network(callback_leave=hue.set_leave_home, callback_join=hue.set_arrive)
    schedule.every().day.at("01:00").do(print_heap, h=heap)
    print_heap(h=heap)
    while True:
        schedule.run_pending()
        time.sleep(60)
