#!/usr/bin/env python
"""Inject management probe-request and data MPDUs on a monitor iface.

Usage:
  wifi-inject-probe.py [wlan0]

Requires the interface already in monitor mode with a channel set, e.g.:
  iw dev wlan0 set type monitor
  iw dev wlan0 set channel 6
"""
from __future__ import print_function

import socket
import sys
import time

from scapy.all import (
	Dot11,
	Dot11Elt,
	Dot11ProbeReq,
	RadioTap,
	RandMAC,
	Raw,
)

iface = sys.argv[1] if len(sys.argv) > 1 else "wlan0"
src = str(RandMAC())


def build_mgmt():
	return bytes(
		RadioTap()
		/ Dot11(type=0, subtype=4, addr1="ff:ff:ff:ff:ff:ff",
			addr2=src, addr3="ff:ff:ff:ff:ff:ff")
		/ Dot11ProbeReq()
		/ Dot11Elt(ID="SSID", info="")
	)


def build_data():
	return bytes(
		RadioTap()
		/ Dot11(type=2, subtype=0, addr1="ff:ff:ff:ff:ff:ff",
			addr2=src, addr3="ff:ff:ff:ff:ff:ff")
		/ Raw(b"AICPROBE")
	)


def send_raw(frame, label, n=3):
	print("%s: %d byte(s) x %d on %s" % (label, len(frame), n, iface))
	sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
	sock.settimeout(1.0)
	try:
		sock.bind((iface, 0))
	except OSError as exc:
		print("bind failed:", exc)
		sock.close()
		return False
	ok = 0
	for i in range(n):
		try:
			sent = sock.send(frame)
			ok += 1
			print("  [%d] sent %d" % (i + 1, sent))
		except socket.timeout:
			print("  [%d] TIMEOUT" % (i + 1,))
		except OSError as exc:
			print("  [%d] OSError: %s" % (i + 1, exc))
		time.sleep(0.05)
	sock.close()
	return ok > 0


print("iface=%s src=%s" % (iface, src))
sys.stdout.flush()
send_raw(build_mgmt(), "1) probe-req", 3)
send_raw(build_data(), "2) data MPDU AICPROBE", 5)
print("done")
