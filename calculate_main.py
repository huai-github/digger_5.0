#!/usr/bin/python3
# coding = utf-8

import datetime
import random

from CoordinateTransf import *
from DiggerModelMecharm import *
from DiggerModelWheel import *
import numpy as np
import globalvar as gl
import time
from globalvar import my_lock

laser_list = []
x_save_list = []
y_save_list = []
h_save_list = []
fir_flg = False
sec_flg = False
thr_flg = False
Debug = False


def sameValList(list):
	"""
	若相邻两个数之间的差小于5厘米，则认为是同一个值
	若列表每个元素斗相同，返回False
	"""
	same_flg = False
	for i in range(len(list) - 1):
		if abs(list[i] - list[i + 1]) < 0.05:
			continue
		else:
			same_flg = True
			break

	return same_flg


def minAlt(values):
	""" 找出列表中V型最低点，返回存放所有v型最小值的列表 """
	min_list = []
	before_is_neg = False
	before_val = values[0]
	for i in range(1, len(values)):
		diff = values[i] - before_val
		if diff >= 0:
			if before_is_neg:
				h_o_min = values[i - 1]
				min_list.append(h_o_min)
				# print("h_o_min", h_o_min)
			before_is_neg = False
			before_val = values[i]
		else:
			before_is_neg = True
			before_val = values[i]
	return min_list


def thread_calculate_func():
	h_val = []
	x_val = []
	y_val = []

	# mid_last = 0
	# mid_2_end_diff = 0.1  # 中点和端点的差值
	""" 等待数据准备 """
	while True:
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--gps_calc--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.GpsCalculatorLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("485线程--gps_calc--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gps_data_valid_flg = gl.get_value("gps_data_valid_flg")
		my_lock.GpsCalculatorLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("485线程--gps_calc--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("485线程--calc_485--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.Calculator485Lock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("485线程--calc_485--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		_485_data_valid_flg = gl.get_value("_485_data_valid_flg")
		my_lock.Calculator485Lock.release()
		with open("lock_log.txt", "a") as file:
			file.write("485线程--calc_485--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("485线程--calc_laser--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.LaserCalculatorLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("485线程--calc_laser--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		laser_data_valid_flg = gl.get_value("laser_data_valid_flg")
		my_lock.LaserCalculatorLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("485线程--calc_laser--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		if gps_data_valid_flg and _485_data_valid_flg and laser_data_valid_flg:
			break
		else:
			print("\r\n计算线程数据-----未准备完成==================================\r\n")
			print("\n！！！！！未准备完成:gps:%s\t 485:%s\t laser:%s\n"
				  % (gps_data_valid_flg, _485_data_valid_flg, laser_data_valid_flg))
		time.sleep(0.1)

	""" 正常工作 """
	while True:
		print("\r\n**************************************** 计算线程已启动 ***************************************\r\n")
		# 初始化全局变量
		calculate_data_valid_flg = False
		o_x = 0
		o_y = 0
		o_h = 0

		time.sleep(0.1)

		# 顶端天线的GPS坐标
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--gps_calc--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.GpsCalculatorLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--gps_calc--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gps_x = gl.get_value("gps_x")
		gps_y = gl.get_value("gps_y")
		gps_h = gl.get_value("gps_h")
		rotZ = gl.get_value("gps_yaw")  # 偏航角
		my_lock.GpsCalculatorLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--gps_calc--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_485--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.Calculator485Lock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_485--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		rotX = gl.get_value("roll_2_di_pan")  # 底盘俯仰
		rotY = gl.get_value("pitch_2_di_pan")  # 底盘翻滚
		da_bi_angle = gl.get_value("roll_2_da_bi")  # pitch_2_da_bi
		xiao_bi_angle = gl.get_value("roll_2_xiao_bi")  # pitch_2_XIAO_bi
		my_lock.Calculator485Lock.release()
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_485--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_laser--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.LaserCalculatorLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_laser--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		dou_laser_len = gl.get_value("dou_laser_len")
		my_lock.LaserCalculatorLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_laser--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		# print("计算输入GPS数据:%s %s %s %s\n: " % (gps_x, gps_y, gps_h, rotZ))

		# 转成了毫米
		gps_x = gps_x * 1000
		gps_y = gps_y * 1000
		gps_h = gps_h * 1000

		orgPos = np.array([gps_x, gps_y, gps_h])

		dou_laser_len = dou_laser_len * 1000
		# print("计算输入大臂倾角: %f 小臂 %f 激光 %f " % (da_bi_angle, xiao_bi_angle, dou_laser_len))
		armParameter = np.array([da_bi_angle, xiao_bi_angle, dou_laser_len])  # 换成数组

		# G点测量坐标
		detGpsPos_G = np.dot(np.array([482471.914, 4042627.65, 68.149]), 1000)

		# O点测量坐标
		detGpsPos_O = np.dot(np.array([482468.997, 4042628.367, 68.217]), 1000)

		# 计算A点GPS坐标
		posAQ = DiggerModelWheel()
		rotAngle = np.array([rotX, rotY, -(180.0 + rotZ)])

		gpsPos_A = CoordinateTransf(orgPos, rotAngle, posAQ[0, :])
		# gpsPos_Q = CoordinateTransf(orgPos, rotAngle, posAQ[1, :])

		# 计算g,j,o点GPS坐标
		posGJO = DiggerModelMecharm(armParameter)  # 王目树修改？

		rotAngle = np.hstack([0, rotY, - (180.0 + rotZ)])

		gpsPos_GJO = np.zeros(shape=(1, 3))
		for i in range(3):
			posTmp = posGJO[i, :]
			rst = CoordinateTransf(gpsPos_A, rotAngle, posTmp)  # 不绕X轴旋转
			gpsPos_GJO = np.vstack([gpsPos_GJO, rst])

		gpsPos_GJO = np.delete(gpsPos_GJO, 0, 0)  # 删除第一行的全0行

		rst_gps_pos_gjo = gpsPos_GJO[0, :] - (detGpsPos_G + np.array([0, 0, -917]))
		# print("o postion  %10.3f %10.3f %10.3f\n" % (gpsPos_GJO[2, 0], gpsPos_GJO[2, 1], gpsPos_GJO[2, 2]))

		if gpsPos_GJO[2, 0] and gpsPos_GJO[2, 1] and gpsPos_GJO[2, 2]:
			o_x = gpsPos_GJO[2, 0]
			o_y = gpsPos_GJO[2, 1]
			o_h = gpsPos_GJO[2, 2]
			with open("laser_h.txt", "a") as file:
				file.write(str(o_h) + "\n")

			""" 高程最低点计算 """
			global fir_flg, sec_flg, thr_flg
			laser_list.append(dou_laser_len)  # 毫米
			if len(laser_list) > 30:  # laser5Hz  间隔6s
				laser_list.pop(0)
				delta = (round(laser_list[-1] - laser_list[0], 3))

				if delta < -20:  # 2厘米
					if fir_flg == False and sec_flg == False and thr_flg == False:
						fir_flg = True
						print(" > True  False  False")
					if fir_flg == True and sec_flg == True and thr_flg == False:
						thr_flg = True
						print(" > True  True  True")

				if delta > 20:
					if fir_flg == True and sec_flg == False and thr_flg == False:
						sec_flg = True
						print(" < True  True  False")

				if fir_flg == True:
					x_save_list.append(o_x)  # 毫米
					y_save_list.append(o_y)
					h_save_list.append(o_h)
				# print(f"h_save_list{h_save_list}\n")

				if fir_flg == True and sec_flg == True and thr_flg == True:
					print(" end True True True")
					# 计算，清空标志位，清理存储区
					h_send = min(h_save_list)
					i = h_save_list.index(h_send)
					x_send = x_save_list[i]
					y_send = y_save_list[i]

					fir_flg = False
					sec_flg = False
					thr_flg = False

					x_save_list.clear()
					y_save_list.clear()
					h_save_list.clear()

					my_lock.Calc4gLock.acquire()
					gl.set_value("o_min_flg", True)
					gl.set_value("x_send", x_send)  # 毫米
					gl.set_value("y_send", y_send)
					gl.set_value("h_send", h_send)
					my_lock.Calc4gLock.release()

			calculate_data_valid_flg = True

		# 设置全局变量
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_win--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.CalculatorWinLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_win--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gl.set_value("calculate_data_valid_flg", calculate_data_valid_flg)
		gl.set_value("o_x", o_x)
		gl.set_value("o_y", o_y)
		gl.set_value("o_h", o_h)
		my_lock.CalculatorWinLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("计算线程--calc_win--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		print("！！！！！计算线程！！！！！%s\n" % datetime.datetime.now().strftime('%H:%M:%S.%f'))
