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


class DataReady(object):
    def __init__(self):
        self.gps_data_ready_flg = False
        self._4g_data_ready_flg = False
        self._485_data_ready_flg = False
        self.laser_data_ready_flg = False
        self.calculate_data_ready_flg = False


data_ready_flg = DataReady()


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
