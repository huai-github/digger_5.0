from CoordinateTransf import *
from DiggerModelMecharm import *
from DiggerModelWheel import *
import numpy as np
import globalvar as gl
import threading
import time
from globalvar import my_lock
from globalvar import data_ready_flg

g_calculate_threadLock = threading.Lock()
values = []


def o_min_altitude(h_o):
	"""根据gps_h计算斗的高度h_o"""
	global values
	values.append(h_o)
	before_is_neg = False
	before_val = values[0]
	for i in range(1, len(values)):
		diff = values[i] - before_val
		if diff >= 0:
			if before_is_neg:
				h_o_min_flag = True
				gl.set_value("h_o_min_flag", h_o_min_flag)  # 挖完一次
				h_o_min = values[i - 1]
				gl.set_value("h_o_min", h_o_min)  # 最低点的值---ui显示、4g发送
			# print("h_o_min", h_o_min)
			before_is_neg = False
			before_val = values[i]
			values = []
		else:  # diff >= 0:
			before_is_neg = True
			before_val = values[i]


def thread_calculate_func():
	"""等待数据准备"""
	time.sleep(0.001)
	while True:
		if data_ready_flg.gps_data_ready_flg and data_ready_flg._485_data_ready_flg and data_ready_flg.laser_data_ready_flg:
			data_ready_flg.gps_data_ready_flg = False
			data_ready_flg._485_data_ready_flg = False
			data_ready_flg.laser_data_ready_flg = False
			break
		else:
			print("\r\n计算线程数据-----未准备完成\r\n")
			print("gps_data_ready_flg:",data_ready_flg.gps_data_ready_flg)
			print("_485_data_ready_flg:",data_ready_flg._485_data_ready_flg)
			print("laser_data_ready_flg:",data_ready_flg.laser_data_ready_flg)


	while True:
		print("\r\n======================================计算线程已启动============================================\r\n")
		time.sleep(0.05)

		# 顶端天线的GPS坐标
		# gps_x = 482471.305
		# gps_y = 4042631.307
		# gps_h = 68.129

		gps_x = gl.get_value("gps_x")
		gps_y = gl.get_value("gps_y")
		gps_h = gl.get_value("gps_h")
		print("计算输入 GPS 数据--------------: ", gps_x, gps_y, gps_h)
		# 转成了毫米
		gps_x = gps_x * 1000
		gps_y = gps_y * 1000
		gps_h = gps_h * 1000

		orgPos = np.array([gps_x, gps_y, gps_h])
		# 检测的旋转角度
		# rotX = -0.46
		# rotY = -0.51
		# rotZ = 37.553

		rotX = gl.get_value("roll_2_di_pan")  # 底盘俯仰
		rotY = gl.get_value("pitch_2_di_pan")  # 底盘翻滚
		rotZ = gl.get_value("gps_yaw")  # 偏航角

		# rotZ = 0
		# print("计算输入 rot 数据: ", rotX, rotY, rotZ)

		# 大臂小臂检测角度
		# da_bi_angle = 9.18
		# xiao_bi_angle = 130.11
		# dou_laser_len = 792
		da_bi_angle = gl.get_value("roll_2_da_bi")  # pitch_2_da_bi
		xiao_bi_angle = gl.get_value("roll_2_xiao_bi")  # pitch_2_XIAO_bi
		dou_laser_len = gl.get_value("dou_laser_len")
		dou_laser_len = dou_laser_len * 1000
		print("计算输入大臂倾角: %f 小臂 %f 激光 %f " % (da_bi_angle, xiao_bi_angle, dou_laser_len))
		armParameter = np.array([da_bi_angle, xiao_bi_angle, dou_laser_len])  # 换成数组

		# G点测量坐标
		detGpsPos_G = np.dot(np.array([482471.914, 4042627.65, 68.149]), 1000)
		# J点测量坐标
		# detGpsPos_J = np.dot(np.array([482475.593, 4042628.693, 67.357]), 1000)
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
		# print("G postion  %10.3f %10.3f %10.3f -------------------"  %(gpsPos_GJO[0, 0],gpsPos_GJO[0, 1],gpsPos_GJO[0, 2] ))
		# print("O postion  %10.3f %10.3f %10.3f +++++++++++++++++++"  %(gpsPos_GJO[2, 0],gpsPos_GJO[2, 1],gpsPos_GJO[2, 2] ))

		if gpsPos_GJO[2, 0] and gpsPos_GJO[2, 1] and gpsPos_GJO[2, 2]:
			gl.set_value("o_x", gpsPos_GJO[2, 0])
			gl.set_value("o_y", gpsPos_GJO[2, 1])
			gl.set_value("o_h", gpsPos_GJO[2, 2])
			# gl.set_value("o_h", 62.948*1000)
			# 计算o点的最低点
			o_min_altitude(rst_gps_pos_gjo[-1])

			data_ready_flg.calculate_data_ready_flg = True
