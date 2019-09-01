import threading

from scapy.all import *

import settings


class Network(object):
    """
    Class to detect changes in network and trigger functions when device joins or leaves
    form network
    """

    def __init__(self, callback_leave, callback_join, track=True):
        """
        Set up network class.

        Keyword arguments:
        callback_join -- Function to trigger when new tracked device joins to network
        callback_leave -- Function to trigger when none of tracked devices are in network
        track -- Start ARP packet sniffing and interval to scan network, default True
        """

        self.handle_leave = callback_leave
        self.handle_join = callback_join
        self._devices_online = set()
        for _ in range(5):
            self.scan_devices()
        if track:
            self._ping_interval = self._set_interval(self.ping_devices_online,
                                                     settings.SCAN_INTERVAL)
            self._sniff = threading.Thread(target=self._start_sniff)
            self._sniff.start()
            if settings.DEBUG:
                print(f"Scanning interval set up with{settings.SCAN_INTERVAL}s")
                print("ARP listening active")

    def scan_devices(self, ip=settings.NETWORK_MASK):
        """
        Scan all devices in network. If initial_scan is True, disable ARP packet handling.
        By default network mask from settings is used, but can be overriden from
        arguments.
        This updates devices_online class variable. If no tracked devices found after
        scan, trigger given leave callback function.
        """

        arp_request = ARP(pdst=ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast/arp_request
        answered_list = srp(arp_request_broadcast, timeout=2, verbose=False)[0]

        for client in answered_list:
            client_mac = str(client[1].hwsrc)
            client_ip = str(client[1].psrc)
            if settings.DEBUG:
                print("found device", client_ip, client_mac)
            if client_mac in settings.DEVICES:
                self._devices_online.add((client_ip, client_mac))

        if settings.DEBUG:
            print("tracked devcices online", self._devices_online)

    def ping_devices_online(self):
        if len(self._devices_online) == 0:
            return

        for device in self._devices_online.copy():
            for _ in range(5):
                ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff") /
                                 ARP(pdst=device[0]), timeout=2, verbose=False)
                if len(ans) > 0:
                    return

            if settings.DEBUG:
                print("lost", device)
            self._devices_online.remove(device)

        if len(self._devices_online) == 0:
            if settings.DEBUG:
                print("All devices offline")
            self.handle_leave()

    def _start_sniff(self):
        sniff(filter="arp", prn=self.handle_arp_packet)

    def handle_arp_packet(self, packet):
        """
        Handle detected ARP packet. If packet is from some of tracked devices specified in
        settings and it is not present in devices online, trigger join callback function
        """

        client_mac = str(packet[1].hwsrc)
        client_ip = str(packet[1].psrc)
        device = (client_ip, client_mac)
        if client_mac in settings.DEVICES and device not in self._devices_online:
            if settings.DEBUG:
                print("new tracked device joined", device)
            self._devices_online.add(device)
            self.handle_join()

    def _set_interval(self, func, sec):
        """
        Set up and start intervall for given function and interval in it's own thread
        """

        def func_wrapper():
            self._set_interval(func, sec)
            func()
        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t
