#!/usr/bin/python3
# coding = utf-8
import threading
import time
from datetime import datetime

from _4g import *
from gps import *
from laser import Laser
from serial_port import SerialPortCommunication
from globalvar import *


def laserCheck(rec_buf):
	sum_rec = sum(rec_buf[:-1])  # 求和
	neg = hex(sum_rec ^ 0xffff)  # 取反
	data = neg[-2:]  # 最后一个字节
	check = int(data, 16) + 1
	# check = hex(check)
	return check


class TimeInterval(object):
	def __init__(self, start_time, interval, callback_proc, args=None, kwargs=None):
		self.__timer = None
		self.__start_time = start_time
		self.__interval = interval
		self.__callback_pro = callback_proc
		self.__args = args if args is not None else []
		self.__kwargs = kwargs if kwargs is not None else {}

	def exec_callback(self, args=None, kwargs=None):
		self.__callback_pro(*self.__args, **self.__kwargs)
		self.__timer = threading.Timer(self.__interval, self.exec_callback)
		self.__timer.start()

	def start(self):
		interval = self.__interval - (datetime.datetime.now().timestamp() - self.__start_time.timestamp())
		# print( interval )
		self.__timer = threading.Timer(interval, self.exec_callback)
		self.__timer.start()

	def cancel(self):
		self.__timer.cancel()
		self.__timer = None


def mid_filter(fil_list):
	""" 中值滤波 """
	rank_list = sorted(fil_list)
	return rank_list[int(len(rank_list) / 2)]


def thread_gps_func():
	# GPS_COM = "com11"
	GPS_COM = "com1"
	GPS_REC_BUF_LEN = 138
	gps_msg_switch = LatLonAlt()
	gps_com = SerialPortCommunication(GPS_COM, 115200, 0.05)

	x_filter_list = []  # 初始化滤波列表
	y_filter_list = []
	h_filter_list = []
	yaw_filter_list = []
	filter_len = 7

	""" 等待数据准备 """
	while True:
		gps_data = GPSINSData()
		gps_rec_buffer = []
		time.sleep(0.001)

		gps_com.rec_data(gps_rec_buffer, GPS_REC_BUF_LEN)  # int
		if gps_data.gps_msg_analysis(gps_rec_buffer):
			gps_msg_switch.latitude, gps_msg_switch.longitude, gps_msg_switch.altitude, \
				gps_msg_switch.yaw, gps_msg_switch.yaw_state = gps_data.gps_typeswitch()

			y, x = LatLon2XY(gps_msg_switch.latitude, gps_msg_switch.longitude)
			h = gps_msg_switch.altitude

			x = round(x, 3)
			y = round(y, 3)
			h = round(h, 3)
			yaw = round(gps_msg_switch.yaw, 3)

			x_filter_list.append(x)
			y_filter_list.append(y)
			h_filter_list.append(h)
			yaw_filter_list.append(yaw)

			# 中值滤波
			x_mid = mid_filter(x_filter_list)
			y_mid = mid_filter(y_filter_list)
			h_mid = mid_filter(h_filter_list)
			yaw_mid = mid_filter(yaw_filter_list)

			if len(x_filter_list) == filter_len:
				gps_x = x_mid
				gps_y = y_mid
				gps_h = h_mid
				gps_yaw = yaw_mid
				gps_data_valid_flg = True

				# 设置全局变量
				with open("lock_log.txt", "a") as file:
					file.write("gps线程" + "\t" + "gps_calc_lock" + "\t" + "in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
				my_lock.GpsCalculatorLock.acquire()
				with open("lock_log.txt", "a") as file:
					file.write("gps线程" + "\t" + "gps_calc_lock" + "\t" + "ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
				gl.set_value("gps_data_valid_flg", gps_data_valid_flg)
				gl.set_value("gps_x", gps_x)
				gl.set_value("gps_y", gps_y)
				gl.set_value("gps_h", gps_h)
				gl.set_value("gps_yaw", gps_yaw)
				my_lock.GpsCalculatorLock.release()
				with open("lock_log.txt", "a") as file:
					file.write("gps线程" + "\t" + "gps_calc_lock" + "\t" + "out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

				break
			else:
				print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx_filter_list:%s\n" % x_filter_list)
				print("yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy_filter_list:%s\n" % y_filter_list)
				print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh_filter_list:%s\n" % h_filter_list)
		else:
			print("！！！！！！gps准备过程解析错误！！！！！！\n")

		time.sleep(0.1)

	""" 正常流程 """
	while True:
		gps_data = GPSINSData()
		gps_rec_buffer = []

		if gps_com.com.is_open:
			gps_is_open_led = True  # gps串口是否打开
			gps_com.rec_data(gps_rec_buffer, GPS_REC_BUF_LEN)  # int

			if gps_data.gps_msg_analysis(gps_rec_buffer):
				gps_msg_switch.latitude, gps_msg_switch.longitude, gps_msg_switch.altitude, \
				gps_msg_switch.yaw, gps_msg_switch.yaw_state = gps_data.gps_typeswitch()

				"""经纬度转高斯坐标"""
				y, x = LatLon2XY(gps_msg_switch.latitude, gps_msg_switch.longitude)
				h = gps_msg_switch.altitude

				x = round(x, 3)
				y = round(y, 3)
				h = round(h, 3)
				yaw = round(gps_msg_switch.yaw, 3)

				x_filter_list.append(x)
				y_filter_list.append(y)
				h_filter_list.append(h)
				yaw_filter_list.append(yaw)

				x_filter_list.pop(0)
				y_filter_list.pop(0)
				h_filter_list.pop(0)
				yaw_filter_list.pop(0)

				# 均值滤波
				x_mid = mid_filter(x_filter_list)
				y_mid = mid_filter(y_filter_list)
				h_mid = mid_filter(h_filter_list)
				yaw_mid = mid_filter(yaw_filter_list)

				# 设置全局变量
				with open("lock_log.txt", "a") as file:
					file.write("gps线程--gps_calc--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + '\n')
				my_lock.GpsCalculatorLock.acquire()
				with open("lock_log.txt", "a") as file:
					file.write("gps线程--gps_calc--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + '\n')
				gl.set_value("gps_x", x_mid)
				gl.set_value("gps_y", y_mid)
				gl.set_value("gps_h", h_mid)
				gl.set_value("gps_yaw", yaw_mid)
				my_lock.GpsCalculatorLock.release()
				with open("lock_log.txt", "a") as file:
					file.write("gps线程--gps_calc--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + '\n')
		else:
			gps_is_open_led = False

		with open("lock_log.txt", "a") as file:
			file.write(str("gps线程--gps_led--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + '\n'))
		my_lock.gpsLedLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write(str("gps线程--gps_led--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + '\n'))
		gl.set_value("gps_is_open_led", gps_is_open_led)
		my_lock.gpsLedLock.release()
		with open("lock_log.txt", "a") as file:
			file.write(str("gps线程--gps_led--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + '\n'))

		time.sleep(0.1)
		print("！！！！！gps线程！！！！！%s\n" % datetime.datetime.now().strftime('%H:%M:%S'))


def thread_4g_func():
	TYPE_HEART = 1  # 消息类型。1：心跳，2：上报
	TYPE_SEND = 2
	# TODO ： 接
	# COM_ID_4G = "com4"
	COM_ID_4G = "com13"
	com_4g = SerialPortCommunication(COM_ID_4G, 115200, 0.1)
	diggerId = 566609996553388032

	# 全局变量初始化
	_4g_data_valid_flg = False

	""" 间隔5秒发送一次心跳 """
	heart = Heart(TYPE_HEART, diggerId)
	heart.send_heart_msg(com_4g)
	start = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
	minute = TimeInterval(start, 5, heart.send_heart_msg, [com_4g])
	minute.start()
	minute.cancel()

	while True:
		_4g_recv_flg = False

		rec_buf = com_4g.read_line()
		# print("==============recv buf %s \n" % rec_buf)
		time.sleep(0.001)
		if rec_buf != b'':
			_4g_recv_flg = True
		else:
			print("\n --4g未接收到任务+++++++++++++++++++++++++++++++++++++++++++ \n")

		if _4g_recv_flg:
			rec_buf_dict = task_switch_dict(rec_buf)  # 转成字典格式

			# 保存xyhw列表
			sx_list, sy_list, sh_list, sw_list, ex_list, ey_list, eh_list, ew_list = get_xyhw(rec_buf_dict)
			if sx_list and sy_list and sh_list and sw_list and ex_list and ey_list and eh_list and ew_list:
				_4g_data_valid_flg = True
				# 设置全局变量
				with open("lock_log.txt", "a") as file:
					file.write("4g线程--win_4g--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
				my_lock.Win4gLock.acquire()
				with open("lock_log.txt", "a") as file:
					file.write("4g线程--win_4g--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
				gl.set_value('g_start_x_list', sx_list)
				gl.set_value('g_start_y_list', sy_list)
				gl.set_value('g_start_h_list', sh_list)
				gl.set_value('g_start_w_list', sw_list)
				gl.set_value('g_end_x_list', ex_list)
				gl.set_value('g_end_y_list', ey_list)
				gl.set_value('g_end_h_list', eh_list)
				gl.set_value('g_end_w_list', ew_list)
				gl.set_value("_4g_data_valid_flg", _4g_data_valid_flg)
				my_lock.Win4gLock.release()
				with open("lock_log.txt", "a") as file:
					file.write("4g线程--win_4g--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
			else:
				print("\n--任务解析失败--\n")

		# 发送o点x,y,h,w
		with open("lock_log.txt", "a") as file:
			file.write("4g线程--calc_4g--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.Calc4gLock.acquire()
		o_min_flg = gl.get_value("o_min_flg")
		with open("lock_log.txt", "a") as file:
			file.write("4g线程--calc_4g--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		o_x_4g = gl.get_value("x_send")  # mm
		o_y_4g = gl.get_value("y_send")
		o_h_4g = gl.get_value("h_send")
		my_lock.Calc4gLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("4g线程--calc_4g--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("4g线程--win4g--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.Win4gLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("4g线程--win4g--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		o_w_flg = gl.get_value("o_w_flg")
		o_w_4g = gl.get_value("o_w_4g")  # Win4gLock
		my_lock.Win4gLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("4g线程--win4g--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		if o_min_flg and o_w_flg:
			send = SendMessage(TYPE_SEND, diggerId, round(o_x_4g / 1000, 3), round(o_y_4g / 1000, 3), round(o_h_4g / 1000, 3), o_w_4g)  # m
			send_msg_json = send.switch_to_json()
			com_4g.send_data(send_msg_json.encode('utf-8'))
			com_4g.send_data('\n'.encode('utf-8'))

			with open("lock_log.txt", "a") as file:
				file.write("4g_线程--calc_4g--in" + datetime.datetime.now().strftime('%H:%M:%S') + '\n')
			my_lock.Calc4gLock.acquire()
			with open("lock_log.txt", "a") as file:
				file.write("4g_线程--calc_4g--ing" + datetime.datetime.now().strftime('%H:%M:%S') + '\n')
			gl.set_value("o_min_flg", False)
			my_lock.Calc4gLock.release()
			with open("lock_log.txt", "a") as file:
				file.write("4g_线程--calc_4g--out" + datetime.datetime.now().strftime('%H:%M:%S') + '\n')

			with open("lock_log.txt", "a") as file:
				file.write("4g线程--win_4g--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
			my_lock.Win4gLock.acquire()
			gl.set_value("o_w_flg", False)
			with open("lock_log.txt", "a") as file:
				file.write("4g线程--win_4g--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
			my_lock.Win4gLock.release()
			with open("lock_log.txt", "a") as file:
				file.write("4g线程--win_4g--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		time.sleep(0.2)
		print("！！！！！4g线程！！！！！%s\n" % datetime.datetime.now().strftime('%H:%M:%S'))


def thread_laser_dou_func():
	# LASER3_COM = "com20"
	LASER3_COM = "com3"
	LASER_REC_BUF_LEN = 11
	laser3 = Laser(LASER3_COM)
	time.sleep(0.01)
	laser_min_distance = 0.1  # 激光安装最小距离
	laserLed = False

	""" 等待数据准备 """
	while True:
		laser_rec_buf = laser3.laser_read_data(LASER_REC_BUF_LEN)
		if laser_rec_buf is not None:
			# 校验
			check_out = laserCheck(laser_rec_buf)
			last_val = int.from_bytes(laser_rec_buf[-1:], byteorder='little', signed=False)
			if check_out == last_val:
				laser3_dist = laser3.get_distance(laser_rec_buf)
				if laser3_dist > laser_min_distance:
					laser_data_valid_flg = True
					# 设置全局变量
					with open("lock_log.txt", "a") as file:
						file.write("激光线程--laser_calc--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
					my_lock.LaserCalculatorLock.acquire()
					with open("lock_log.txt", "a") as file:
						file.write("激光线程--laser_calc--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
					gl.set_value("dou_laser_len", laser3_dist)
					gl.set_value("laser_data_valid_flg", laser_data_valid_flg)
					my_lock.LaserCalculatorLock.release()
					with open("lock_log.txt", "a") as file:
						file.write("激光线程--laser_calc--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
					break
				else:
					print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLdou_laser_len:%s\n" % laser3_dist)
			else:
				print("!!!!!!!激光校验失败!!!!!!\n")
		time.sleep(0.05)

	""" 正常流程 """
	while True:
		if laser3.com_laser.com.is_open:
			laser_rec_buf = laser3.laser_read_data(LASER_REC_BUF_LEN)
			if laser_rec_buf is not None:
				# 校验
				check_out = laserCheck(laser_rec_buf)
				last_val = int.from_bytes(laser_rec_buf[-1:], byteorder='little', signed=False)
				if check_out == last_val:
					laser3_dist = laser3.get_distance(laser_rec_buf)
					if laser3_dist > laser_min_distance:
						# print("=======================挖斗激光%f" % laser3_dist)
						dou_laser_len = laser3_dist
						laserLed = True
						# 设置全局变量
						with open("lock_log.txt", "a") as file:
							file.write("激光线程--laser_calc--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
						my_lock.LaserCalculatorLock.acquire()
						with open("lock_log.txt", "a") as file:
							file.write("激光线程--laser_calc--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
						gl.set_value("dou_laser_len", dou_laser_len)
						my_lock.LaserCalculatorLock.release()
						with open("lock_log.txt", "a") as file:
							file.write("激光线程--laser_calc--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
					else:
						laserLed = False
						print("激光距离错误\n")
				else:
					laserLed = False
					print("！！！！！ 激光校验失败 ！！！！\n")
		else:
			laserLed = False
		# 设置全局变量
		with open("lock_log.txt", "a") as file:
			file.write("激光线程--laser_led--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.laserLedLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("激光线程--laser_led--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gl.set_value("laserLed", laserLed)
		my_lock.laserLedLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("激光线程--laser_led--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		time.sleep(0.15)
		print("！！！！！laser线程！！！！！%s\n" % datetime.datetime.now().strftime('%H:%M:%S'))

