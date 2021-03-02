#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading


class MyLock(object):
    def __init__(self):
        self.GpsCalculatorLock = threading.Lock()
        self._4gUiLock = threading.Lock()
        self.LaserCalculatorLock = threading.Lock()
        self._485CalculatorLock = threading.Lock()
        self.CalculatorUiLock = threading.Lock()


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
