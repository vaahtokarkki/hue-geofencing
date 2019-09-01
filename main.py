#!/usr/bin/env python3
from hue import Hue
from network import Network

if __name__ == "__main__":
    hue = Hue()
    network = Network(callback_leave=hue.set_leave_home, callback_join=hue.set_arrive)
