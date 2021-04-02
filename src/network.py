import ipaddress
import logging
import subprocess
import threading
import time
from subprocess import PIPE, Popen

import schedule
from scapy.all import ARP, ICMP, IP, TCP, Ether, sniff, sr1, srp

from src.settings import (BLUETOOTH_DEVICES, DEVICES, NETWORK_MASK,
                          PING_SCHEDULE, SCAN_INTERVAL)

MAX_PING_TRIES = 5  # How many times a device is pinged
log = logging.getLogger("main")


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

        self.handle_leave = callback_leave
        self.handle_join = callback_join
        self._devices_online = set()
        self._discovered_hosts = set()
        self._stop_sniff = threading.Event()
        if track:
            log.info("Tracking active")

            # A lock to prevent multiple ping calls at the same time
            self._ping_running = False

            schedule.every(SCAN_INTERVAL).minutes.do(self.ping_devices_online)
            schedule.every(SCAN_INTERVAL*2).minutes.do(self.scan_devices_bluetooth)
            if PING_SCHEDULE:
                schedule.every(1).hours.do(self.scan_devices)

            self._scheduler = threading.Thread(target=self._run_schedule).start()
            self._sniff = threading.Thread(target=self._run_sniff).start()
            self.scan_devices()

    def scan_devices(self, ip=NETWORK_MASK):
        """
        Scan all devices in network. By default network mask from settings is used, but
        can be overridden from arguments. Found devices are handled as normal packets in
        handle packet method.
        """
        def ping(host):
            log.debug(f"Ping host {host}")
            subprocess.call(["ping", "-c", "1", str(host)], shell=False,
                            stdout=subprocess.DEVNULL)

        log.debug("Staring ping")
        for host in self._discovered_hosts:
            ping(host)

        if self._all_devices_online():
            return

        subnetmask_hosts = [host for host in ipaddress.ip_network(ip).hosts()]
        for host in subnetmask_hosts:
            ping(host)

    def scan_devices_bluetooth(self):
        """ Ping all bluetooth devices, even those which are offline """
        if self._ping_running:
            return False

        self._ping_running = True
        for device in DEVICES():
            address = self._resolve_bt_mac(device)
            if self._ping_device_bluetooth(address):
                self._devices_online.add((address))
        self._ping_running = False

    def ping_devices_online(self):
        """
        Ping all devices in devices_online. Return True if device is responding, otherwise
        False and remove device from devices_online set. If all devices are removed from
        set, trigger handle_leave callback function
        """
        if not self._devices_online or self._ping_running:
            return False

        self._ping_running = True
        for device in self._devices_online.copy():
            if len(device) == 1:  # Device has only bt mac address
                if self._ping_device_bluetooth(device):
                    continue
            else:
                if self._ping_device(device[0]) or self._ping_device_bluetooth(device[1]):
                    continue

            log.info(f"Lost device {device}")
            self._devices_online.remove(device)
            self._stop_sniff.clear()

        if not self._devices_online:
            log.info("All devices offline")
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
        log.debug(f'Packet: {client_ip}, {client_mac}')
        if not self._is_device_online(client_mac) and client_ip != "0.0.0.0":
            device = (client_ip, client_mac)
            log.info(f"new tracked device joined {device}")
            self._devices_online.add(device)
            self._discovered_hosts.add(client_ip)
            self.handle_join()
            if self._all_devices_online():
                self._stop_sniff.set()

    def _ping_device_bluetooth(self, device, tries=MAX_PING_TRIES):
        """
        Ping Bluetooth device

        Core arguments:
        device -- Device as wifi mac, bluetooth mac is resolved from settings
        """
        bluetooth_mac = self._resolve_bt_mac(device)
        if not bluetooth_mac:
            return False

        for _ in range(tries):
            p = Popen(["l2ping", "-c", "5", "-t", "2", str(bluetooth_mac)], stdout=PIPE,
                      stderr=PIPE, close_fds=True)
            p.communicate()

            if p.returncode == 0:
                log.debug(f"Host {bluetooth_mac} is up, responding to bluetooth")
                return True

        return False

    def _run_sniff(self):
        """ Run scapy network sniff with BPF filter """
        while True:
            if not self._stop_sniff.isSet():
                log.debug("Sniffing started")
                sniff(filter=self._get_BPF_filter(), prn=self.handle_packet, store=False,
                      stop_filter=self._should_stop_sniff)
                log.debug("Sniffing stopped")
            time.sleep(60)

    def _should_stop_sniff(self, packet):
        return self._stop_sniff.isSet()

    def _ping_device(self, device):
        """
        Ping given device with multiple different methods on network layer. If device is
        responding return True, otherwise False.

        Ping is done with following steps:
            1. Ping with ARP packet
            2. Ping ICMP echo packet
            3. Ping with TCP packets to ports 5353 and 62078.
               (Used in iPhone for Bonjour service and wifi-sync)

        Core arguments:
            device -- Device ip address as string, for example '192.168.1.101'
        Returns:
            boolean --- If device is responding
        """

        if not device:
            return False

        ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=device), retry=5,
                         timeout=2, verbose=False)
        if ans:
            log.debug(f"Host {device} is up, responding to ARP")
            return True

        ans = sr1(IP(dst=device)/ICMP(), retry=5, timeout=2, verbose=False)
        if ans:
            log.debug(f"Host {device} is up, responding to ICMP Echo")
            return True

        ans = sr1(IP(dst=device)/TCP(dport=[5353, 62078]), retry=5, timeout=1,
                  verbose=False)
        if ans:
            log.debug(f"Host {device} is up, responding to ICP port 62078")
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
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(5)
            except Exception as e:
                log.error(f"Scheduler failed: {e}")

    def _all_devices_online(self):
        """ Return True if all residents are currently at home """
        return len(DEVICES()) == len(self._devices_online)

    def _is_device_online(self, mac_address):
        """ Check is device online based on WiFi mac address """
        return any(mac == mac_address for ip, mac in self._devices_online)
