import threading
from datetime import datetime
from gyro import *
from laser import Laser
from serial_port import SerialPortCommunication
from _4g import *
from gps import *

g_x = 0  # gps->4g
g_y = 0
g_h = 0

g_gps_threadLock = threading.Lock()
g_4g_threadLock = threading.Lock()
g_gyro2_da_bi_threadLock = threading.Lock()
g_gyro2_xiao_bi_threadLock = threading.Lock()
g_gyro3_threadLock = threading.Lock()
g_laser_da_bi_threadLock = threading.Lock()
g_laser2_xiao_bi_threadLock = threading.Lock()
g_laser3_dou_threadLock = threading.Lock()


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
	GPS_COM = "com3"
	GPS_REC_BUF_LEN = 138
	while True:
		gps_data = GPSINSData()
		gps_msg_switch = GpsMsg()
		gps_rec_buffer = []
		gps_com = SerialPortCommunication(GPS_COM, 115200, 0.2)  # 5Hz
		gps_com.rec_data(gps_rec_buffer, GPS_REC_BUF_LEN)  # int
		gps_com.close_com()

		g_gps_threadLock.acquire()  # 加锁

		data_right_flag = gps_data.gps_msg_analysis(gps_rec_buffer)
		if data_right_flag:
			gps_msg_switch.latitude, gps_msg_switch.longitude, gps_msg_switch.altitude, \
				gps_msg_switch.yaw,  gps_msg_switch.yaw_state = gps_data.gps_union_switch()
			print("纬度：%s\t经度：%s\t海拔：%s\t" % (gps_msg_switch.latitude, gps_msg_switch.longitude, gps_msg_switch.altitude))
			print("偏航角：", gps_msg_switch.yaw)

			# 经纬度转高斯坐标
			global g_x, g_y, g_h
			g_x, g_y = LatLon2XY(gps_msg_switch.latitude, gps_msg_switch.longitude)
			g_h = gps_msg_switch.altitude
			gl.set_value("gps_x", g_x)
			gl.set_value("gps_y", g_y)
			gl.set_value("gps_h", g_h)  # to calculate_main.py

			print("x:%s\ty:%s\t%s" % (g_x, g_y, g_h))

		else:
			print("gps data error\n")

		g_gps_threadLock.release()  # 解锁


def thread_4g_func():
	TYPE_HEART = 1  # 消息类型。1：心跳，2：上报
	TYPE_SEND = 2
	diggerId = 539081892037656576  # 挖掘机ID
	COM_ID_4G = "com5"

	heart = Heart(TYPE_HEART, diggerId)
	com_4g = SerialPortCommunication(COM_ID_4G, 115200, 0.5)

	""" 间隔一分钟发送一次心跳 """
	start = datetime.now().replace(minute=0, second=0, microsecond=0)
	minute = TimeInterval(start, 60, heart.send_heart_msg, [com_4g])
	minute.start()
	minute.cancel()

	while True:
		h_o_min_flag = gl.get_value("h_o_min_flag")

		""" 接受任务 """
		g_4g_threadLock.acquire()  # 加锁
		rec_buf = com_4g.read_line()
		if rec_buf != b'':
			rec_buf_dict = task_switch_dict(rec_buf)  # 转成字典格式
			# 保存挖掘机ID
			digger_id = rec_buf_dict['diggerId']
			gl.set_value("diggerId", digger_id)
			# 保存xyhw列表
			sx_list, sy_list, sh_list, sw_list, ex_list, ey_list, eh_list, ew_list = get_xyhw(rec_buf_dict)
			gl.set_value('g_start_x_list', sx_list)
			gl.set_value('g_start_y_list', sy_list)
			gl.set_value('g_start_h_list', sh_list)
			gl.set_value('g_start_w_list', sw_list)
			gl.set_value('g_end_x_list', ex_list)
			gl.set_value('g_end_y_list', ey_list)
			gl.set_value('g_end_h_list', eh_list)
			gl.set_value('g_end_w_list', ew_list)

			# 任务接收完成标志
			received_flag = True
			gl.set_value("received_flag", received_flag)
		else:
			print("！！4g receive error！！\n")

		""" 信息上报 """
		if h_o_min_flag:  # 得到最低点
			h_o_min = gl.get_value("h_o_min")
			# 发送x,y,h,w
			send = SendMessage(TYPE_SEND, diggerId, round(g_x, 3), round(g_y, 3), round(h_o_min, 3), 0)
			send_msg_json = send.switch_to_json()
			com_4g.send_data(send_msg_json.encode('utf-8'))
			# 清空h_o_min_flag标志位
			h_o_min_flag = False
			gl.set_value("h_o_min_flag", h_o_min_flag)

		g_4g_threadLock.release()  # 解锁


def thread_gyro2_da_bi_func():
	GYRO_COM = "com32"
	gyro = Gyro2(GYRO_COM)
	while True:
		g_gyro2_da_bi_threadLock.acquire()
		angle = gyro.get_angle()
		roll = angle[0]
		pitch = angle[1]

		if roll is not None and pitch is not None:
			gl.set_value("roll_2_da_bi", roll)
			gl.set_value("pitch_2_da_bi", pitch)
			print("roll_2_da_bi:", roll)
			print("pitch_2_da_bi:", pitch)
		g_gyro2_da_bi_threadLock.release()


def thread_gyro2_xiao_bi_func():
	GYRO_COM = "com38"
	gyro = Gyro2(GYRO_COM)
	while True:
		g_gyro2_xiao_bi_threadLock.acquire()
		angle = gyro.get_angle()
		roll = angle[0]
		pitch = angle[1]

		if roll is not None and pitch is not None:
			gl.set_value("roll_2_xiao_bi", roll)
			gl.set_value("pitch_2_xiao_bi", pitch)
			print("roll_2_xiao_bi:", roll)
			print("pitch_2_xiao_bi:", pitch)
		g_gyro2_xiao_bi_threadLock.release()


def thread_gyro3_func():
	GYRO_COM = "com32"
	gyro = Gyro3(GYRO_COM)
	while True:
		g_gyro3_threadLock.acquire()
		angle = gyro.get_angle()
		roll = angle[0]
		pitch = angle[1]
		yaw = angle[2]

		if roll is not None and pitch is not None and yaw is not None:
			gl.set_value("roll_3", roll)
			gl.set_value("pitch_3", pitch)
			gl.set_value("yaw_3", yaw)
			print("roll_3:", roll)
			print("pitch_3:", pitch)
			print("yaw_3:", yaw)
		g_gyro3_threadLock.release()


def thread_laser_da_bi_func():
	LASER1_COM = "com37"
	laser1 = Laser(LASER1_COM)
	while True:
		g_laser_da_bi_threadLock.acquire()
		laser1_dist = laser1.get_distance()
		if laser1_dist is not None:
			gl.set_value("da_bi_laser_len", laser1_dist)
			print("da_bi_laser_len", laser1_dist)
		g_laser_da_bi_threadLock.release()


def thread_laser_xiao_bi_func():
	LASER2_COM = "com38"
	laser2 = Laser(LASER2_COM)
	while True:
		g_laser2_xiao_bi_threadLock.acquire()
		laser2_dist = laser2.get_distance()
		if laser2_dist is not None:
			gl.set_value("xiao_bi_laser_len", laser2_dist)
			print("xiao_bi_laser_len", laser2_dist)
		g_laser2_xiao_bi_threadLock.release()


def thread_laser_dou_func():
	LASER3_COM = "com39"
	laser3 = Laser(LASER3_COM)
	while True:
		g_laser3_dou_threadLock.acquire()
		laser3_dist = laser3.get_distance()
		if laser3_dist is not None:
			gl.set_value("dou_laser_len", laser3_dist)
			print("dou_laser_len", laser3_dist)
		g_laser3_dou_threadLock.release()





