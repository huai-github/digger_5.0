#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading

LOCKLOG = True


class MyLock(object):
    def __init__(self):
        self.GpsCalculatorLock = threading.RLock()
        self.Win4gLock = threading.RLock()
        self.LaserCalculatorLock = threading.RLock()
        self.Calculator485Lock = threading.RLock()
        self.CalculatorWinLock = threading.RLock()
        self.CalculatorUiLock = threading.RLock()
        self.WinUiLock = threading.RLock()
        self.Calc4gLock = threading.RLock()

        self.gpsStableLedLock = threading.RLock()
        self.gpsLedLock = threading.RLock()
        self.laserLedLock = threading.RLock()
        self.gyroLedLock = threading.RLock()


my_lock = MyLock()


def gl_init():
    global _global_dict
    _global_dict = {}


def set_value(name, value):
    _global_dict[name] = value


def get_value(name, defValue = 0):
    try:
        return _global_dict[name]
    except KeyError:
        return defValue
