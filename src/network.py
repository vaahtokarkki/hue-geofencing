import logging
import threading

from scapy.all import *

from src.settings import SCAN_INTERVAL, DEVICES, NETWORK_MASK

SCAN_INTERVAL = SCAN_INTERVAL
REFRESH_INTERVAL = 900
MAX_ARP_TRIES = 5  # How many times ARP ping is sent to one device


class Network(object):
    """
    Class to detect changes in network and trigger functions when device joins or leaves
    form network. Provides also interval functionality to scan devices in network
    periodically.
    """

    def __init__(self, callback_leave, callback_join, track=True):
        """
        Set up network class and create intervals.

        Keyword arguments:
        callback_join -- Function to trigger when new tracked device joins to network
        callback_leave -- Function to trigger when none of tracked devices are in network
        track -- Start ARP packet sniffing and interval to scan network, default True
        """

        self.log = logging.getLogger("main")
        self.handle_leave = callback_leave
        self.handle_join = callback_join
        self._devices_online = set()
        self.refresh_devices_online()
        if track:
            self._ping_interval = self._set_interval(self.ping_devices_online,
                                                     SCAN_INTERVAL)
            self._refresh_interval = self._set_interval(self.refresh_devices_online,
                                                        REFRESH_INTERVAL)
            self._stop_sniff = threading.Event()
            self._sniff = threading.Thread(target=self._start_sniff,
                                           args=[self._stop_sniff])
            self._sniff.start()
            self.log.info(f"Scanning interval set up with{SCAN_INTERVAL}s")
            self.log.info(f"Refresh interval set up with{REFRESH_INTERVAL}s")
            self.log.info("ARP listening active")

    def scan_devices(self, ip=NETWORK_MASK):
        """
        Scan all devices in network. By default network mask from settings is used, but
        can be overriden from arguments. Found devices are added to devices_online class
        variable.
        """

        arp_request = ARP(pdst=ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast/arp_request
        answered_list = srp(arp_request_broadcast, timeout=2, verbose=False)[0]
        for client in answered_list:
            client_mac = str(client[1].hwsrc)
            client_ip = str(client[1].psrc)
            if client_mac in DEVICES():
                self.log.debug(f"found device {client_ip} {client_mac}")
                self._devices_online.add((client_ip, client_mac))

        self.log.debug(f"tracked devcices online {self._devices_online}")

    def refresh_devices_online(self):
        """ Run scan_devices() for given times """
        for _ in range(MAX_ARP_TRIES):
            self.scan_devices()

    def ping_devices_online(self):
        """
        Ping all devices in devices_online. Return True if device is responding, otherwise
        False and remove device from devices_online set. If all devices are removed from
        set, trigger handle_leave callback function
        """
        if len(self._devices_online) == 0:
            return False

        for device in self._devices_online.copy():
            if self._ping_device(device[0]):
                continue

            self.log.warning("Lost device", device)
            self._devices_online.remove(device)

        if len(self._devices_online) == 0:
            self.log.warning("All devices offline")
            self.handle_leave()

    def _start_sniff(self, stop_event):
        """ Run scapy network sniff with ARP filter """
        while not stop_event.is_set():
            sniff(filter=self._get_BPF_filter(), prn=self.handle_packet)

    def _ping_device(self, device):
        """ Ping given device with ARP packets. If device is respondin return True,
        otherwise Flase.

        Core arguments:
        device -- Device ip address as string, for example '192.168.1.101'
        """

        if not device:
            return False

        for _ in range(MAX_ARP_TRIES):
            ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff") /
                             ARP(pdst=device), timeout=2, verbose=False)
            if len(ans) > 0:
                return True
        return False

    def handle_packet(self, packet):
        """
        Handle detected packet. If source of packet is not present in devices online,
        trigger join callback function.

        Note: packets must be filtered with _get_BPF_filter() before handling
        """

        if IP not in packet or Ether not in packet:
            return False

        client_mac = str(packet[Ether].src)
        client_ip = str(packet[IP].src)
        device = (client_ip, client_mac)
        if device not in self._devices_online and client_ip != "0.0.0.0":
            self.log.warning(f"new tracked device joined {device}")
            self._devices_online.add(device)
            self.handle_join()
            if len(self._devices_online) == len(DEVICES()):
                # All devices online, no need to sniff new devices
                self._stop_sniff.set()

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

    def _get_BPF_filter(self):
        """
        Return BPF filter to be used with scapy sniff(). Filter matches all packets with
        source mac in tracked devices given in settings.
        """

        output = ""
        for i in range(len(DEVICES())):
            mac_address = DEVICES()[i]
            output += f"ether src host {mac_address}"
            if i < len(DEVICES()) - 1:
                output += " or "
        return output
