import threading
from datetime import datetime
from gyro import *
from laser import Laser
from serial_port import SerialPortCommunication
from _4g import *
from gps import *
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QDateTime
from time import sleep
import time
from globalvar import my_lock
from globalvar import data_ready_flg


g_x = 0  # gps->4g
g_y = 0
g_h = 0


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
		interval = self.__interval - (datetime.now().timestamp() - self.__start_time.timestamp())
		# print( interval )
		self.__timer = threading.Timer(interval, self.exec_callback)
		self.__timer.start()

	def cancel(self):
		self.__timer.cancel()
		self.__timer = None


def thread_gps_func():
	GPS_COM = "com11"
	GPS_REC_BUF_LEN = 138
	data_right_flag = None
	while True:
		gps_data = GPSINSData()
		gps_msg_switch = LatLonAlt()
		gps_rec_buffer = []
		gps_com = SerialPortCommunication(GPS_COM, 115200, 0.2)  # 5Hz
		gps_com.rec_data(gps_rec_buffer, GPS_REC_BUF_LEN)  # int
		gps_com.close_com()

		data_right_flag = gps_data.gps_msg_analysis(gps_rec_buffer)
		if data_right_flag:
			gps_msg_switch.latitude, gps_msg_switch.longitude, gps_msg_switch.altitude, \
			gps_msg_switch.yaw, gps_msg_switch.yaw_state = gps_data.gps_typeswitch()
			"""经纬度转高斯坐标"""
			global g_x, g_y, g_h
			g_y, g_x = LatLon2XY(gps_msg_switch.latitude, gps_msg_switch.longitude)
			g_h = gps_msg_switch.altitude

			g_x = round(g_x, 3)
			g_y = round(g_y, 3)
			g_h = round(g_h, 3)

			x_org = gl.get_value("gps_x")
			if x_org > 0.1:
				if abs(x_org - g_x) > 10:
					pass
				else:
					gl.set_value("gps_x", g_x)
			else:
				gl.set_value("gps_x", g_x)

			y_org = gl.get_value("gps_y")
			if y_org > 0.1:
				if abs(y_org - g_y) > 10:
					pass
				else:
					gl.set_value("gps_y", g_y)
			else:
				gl.set_value("gps_y", g_y)

			if 0.1 < g_h:
				gl.set_value("gps_h", g_h)
			else:
				pass

			gps_msg_switch.yaw = round(gps_msg_switch.yaw, 3)
			print("平面坐标:  %s\t %s\t %s  偏航角度 %s " % (g_x, g_y, g_h, gps_msg_switch.yaw))

			if g_x and g_y and g_h and gps_msg_switch.yaw:
				data_ready_flg.gps_data_ready_flg = True

		time.sleep(0.1)


def thread_4g_func():
	TYPE_HEART = 1  # 消息类型。1：心跳，2：上报
	TYPE_SEND = 2
	diggerId = 561620038054838272  # 挖掘机ID
	COM_ID_4G = "com4"

	heart = Heart(TYPE_HEART, diggerId)
	com_4g = SerialPortCommunication(COM_ID_4G, 115200, 0.5)
	heart.send_heart_msg(com_4g)
	""" 间隔一分钟发送一次心跳 """
	start = datetime.now().replace(minute=0, second=0, microsecond=0)
	minute = TimeInterval(start, 60, heart.send_heart_msg, [com_4g])
	minute.start()
	minute.cancel()

	"""一直等待直到接到到任务"""
	while True:
		rec_buf = com_4g.read_line()
		print("==============recv buf \n", rec_buf)
		if rec_buf != b'':
			break
		else:
			print("！！4g receive error！！\n")

	"""解析任务"""
	rec_buf_dict = task_switch_dict(rec_buf)  # 转成字典格式
	# 保存挖掘机ID
	if rec_buf_dict:
		digger_id = rec_buf_dict['diggerId']
		gl.set_value("diggerId", digger_id)

	# 保存xyhw列表
	sx_list, sy_list, sh_list, sw_list, ex_list, ey_list, eh_list, ew_list = get_xyhw(rec_buf_dict)
	if sx_list and sy_list and sh_list and sw_list and ex_list and ey_list and eh_list and ew_list:
		gl.set_value('g_start_x_list', sx_list)
		gl.set_value('g_start_y_list', sy_list)
		gl.set_value('g_start_h_list', sh_list)
		gl.set_value('g_start_w_list', sw_list)
		gl.set_value('g_end_x_list', ex_list)
		gl.set_value('g_end_y_list', ey_list)
		gl.set_value('g_end_h_list', eh_list)
		gl.set_value('g_end_w_list', ew_list)

		# 任务接收完成标志
		gl.set_value("taskAnalysisFlg", True)

		data_ready_flg._4g_data_ready_flg = True

	else:
		print("\r\n--任务解析失败--\r\n")

	""" 信息上报 """
	# if h_o_min_flag:  # 得到最低点
	###########################################################################################################
	h_o_min = gl.get_value("h_o_min")
	# 发送x,y,h,w
	send = SendMessage(TYPE_SEND, diggerId, round(g_x, 3), round(g_y, 3), round(h_o_min, 3), 0)
	send_msg_json = send.switch_to_json()
	# com_4g.send_data(send_msg_json.encode('utf-8'))
	###########################################################################################################
	time.sleep(0.1)


def thread_laser_dou_func():
	LASER3_COM = "com20"
	laser3 = Laser(LASER3_COM)
	while True:
		laser3_dist = laser3.get_distance()
		if laser3_dist:
			gl.set_value("dou_laser_len", laser3_dist)
			data_ready_flg.laser_data_ready_flg = True
			# print("挖斗激光", laser3_dist)
		time.sleep(0.1)
