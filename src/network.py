import logging
import threading
import time
from subprocess import PIPE, Popen

import schedule
from scapy.all import ARP, ICMP, IP, TCP, Ether, sniff, sr1, srp

from src.settings import (BLUETOOTH_DEVICES, DEVICES, NETWORK_MASK,
                          SCAN_INTERVAL)

MAX_PING_TRIES = 5  # How many times a device is pinged


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
        self._stop_sniff = threading.Event()
        self.scan_devices()
        if track:
            self.log.info("Tracking active")
            self._ping_running = False  # Lock to prevent multiple ping devices calls
            schedule.every(SCAN_INTERVAL).minutes.do(self.ping_devices_online)
            self._scheduler = threading.Thread(target=self._run_schedule).start()
            self._sniff = threading.Thread(target=self._run_sniff).start()
            self.log.info(f"Scanning interval set up with {SCAN_INTERVAL} min")

    def scan_devices(self):
        """ Run _scan_network() for given times """
        for _ in range(MAX_PING_TRIES):
            self._scan_network()

    def ping_devices_online(self):
        """
        Ping all devices in devices_online. Return True if device is responding, otherwise
        False and remove device from devices_online set. If all devices are removed from
        set, trigger handle_leave callback function
        """
        # Add lock boolean variable to prevent multiple pingings
        if not self._devices_online or self._ping_running:
            return False

        self._ping_running = True
        for device in self._devices_online.copy():
            if self._ping_device(device[0]) or self._ping_device_bluetooth(device[1]):
                continue

            self.log.info(f"Lost device {device}")
            self._devices_online.remove(device)
            self._stop_sniff.clear()

        if not self._devices_online:
            self.log.info("All devices offline")
            self.handle_leave()
        self._ping_running = False

    def handle_packet(self, packet):
        """
        Handle detected packet. If source of packet is not present in devices online,
        trigger join callback function.

        Note: packets must be filtered with _get_BPF_filter() before handling
        """

        if IP not in packet or Ether not in packet:
            return

        client_mac = str(packet[Ether].src)
        client_ip = str(packet[IP].src)
        device = (client_ip, client_mac)
        if device not in self._devices_online and client_ip != "0.0.0.0":
            self.log.info(f"new tracked device joined {device}")
            self._devices_online.add(device)
            self.handle_join()
            if self._all_devices_online():
                self._stop_sniff.set()

    def _ping_device_bluetooth(self, device):
        """
        Ping Bluetooth device

        Core arguments:
        device -- Device as wifi mac, bluetooth mac is resolved from settings
        """
        bluetooth_mac = self._resolve_bt_mac(device)
        if not bluetooth_mac:
            return False

        p = Popen(["l2ping", "-c", "5", "-t", "2", str(bluetooth_mac)], stdout=PIPE,
                  stderr=PIPE, close_fds=True)
        p.communicate()

        if p.returncode != 0:
            return False

        self.log.debug(f"Host {bluetooth_mac} is up, responding to bluetooth")
        return True

    def _run_sniff(self):
        """ Run scapy network sniff with ARP filter """
        while True:
            if not self._stop_sniff.isSet():
                self.log.debug("Sniffing started")
                sniff(filter=self._get_BPF_filter(), prn=self.handle_packet, store=False,
                      stop_filter=self._should_stop_sniff)
                self.log.debug("Sniffing stoped")
            time.sleep(60)

    def _should_stop_sniff(self, packet):
        return self._stop_sniff.isSet()

    def _ping_device(self, device):
        """ Ping given device with ICMP echo packets. If device is respondin return True,
        otherwise Flase.

        Core arguments:
        device -- Device ip address as string, for example '192.168.1.101'
        """

        if not device:
            return False

        ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=device), retry=10,
                         timeout=2, verbose=False)
        if ans:
            self.log.debug(f"Host {device} is up, responding to ARP")
            return True

        ans = sr1(IP(dst=device)/ICMP(), retry=10, timeout=2, verbose=False)
        if ans:
            self.log.debug(f"Host {device} is up, responding to ICMP Echo")
            return True

        ans = sr1(IP(dst=device)/TCP(dport=[5353, 62078]), retry=20, timeout=1,
                  verbose=False)
        if ans:
            self.log.debug(f"Host {device} is up, responding to ICP port 62078")
        return bool(ans)

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

    def _resolve_bt_mac(self, wifi_mac):
        try:
            return BLUETOOTH_DEVICES()[wifi_mac]
        except KeyError:
            return None

    def _run_schedule(self):
        """
        Start loop for scheduler. This should be run at own thread to prevent blocking
        """

        while True:
            schedule.run_pending()
            time.sleep(60)

    def _scan_network(self, ip=NETWORK_MASK):
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
        if self._all_devices_online():
            self._stop_sniff.set()

    def _all_devices_online(self):
        """ Return True if all residents are currently at home """
        return len(DEVICES()) == len(self._devices_online)
