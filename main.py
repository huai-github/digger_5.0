#!/usr/bin/python3
# coding = utf-8

import random
import sys
import threading
from time import sleep

import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QBrush, QImage, QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QWidget

import digger_ui
import multi_thread
import globalvar as gl
from my_thread import MyThread

g_ui_threadLock = threading.Lock()
h = 480  # 画布大小
w = 550

x_min = 0
y_min = 0
x_max = 0
y_max = 0

zoom_x = 0
zoom_y = 0
delta = 5


def isInParRect(x1, y1, x4, y4, x, y):
	# （x1，y1）为最左的点、（x2，y2）为最上的点、（x3，y3）为最下的点、（x4， y4）为最右的点
	# 按顺时针点的位置依次为1，2，4，3
	if x <= x1:
		return False
	if x >= x4:
		return False
	if y >= y1:
		return False
	if y <= y4:
		return False
	return True


# 判断特殊矩形：矩形的边平行于坐标轴
def isInRect(x1, y1, x2, y2, x3, y3, x4, y4, x, y):
	# 使一般矩形旋转，使之平行于坐标轴
	# （x1，y1）为最左的点、（x2，y2）为最上的点、（x3，y3）为最下的点、（x4， y4）为最右的点
	# 按顺时针点的位置依次为1，2，4，3

	if x1 != x4:
		# 坐标系以(x3, y3)为中心，逆时针旋转t至(x4, y4)
		dx = x4 - x3
		dy = y4 - y3
		ds = (dx ** 2 + dy ** 2) ** 0.5
		cost = dx / ds
		sint = dy / ds
		# python特性：隐含临时变量存储值
		x, y = cost * x + sint * y, -sint * x + cost * y
		x1, y1 = cost * x1 + sint * y1, -sint * x1 + cost * y1
		x4, y4 = cost * x4 + sint * y4, -sint * x4 + cost * y4
	return isInParRect(x1, y1, x4, y4, x, y)


def gps_warning_led(qp, color, x, y):
	qp.setPen(color)
	brush = QBrush(Qt.SolidPattern)
	qp.setBrush(brush)
	qp.setBrush(color)
	qp.drawEllipse(int(x), int(y), 50, 50)


def border_warning_led(qp, color, x, y):
	qp.setPen(color)
	brush = QBrush(Qt.SolidPattern)
	qp.setBrush(brush)
	qp.setBrush(color)
	qp.drawEllipse(int(x), int(y), 50, 50)


class MyWindows(QWidget, digger_ui.Ui_Digger):
	def __init__(self):
		super().__init__()
		self.setupUi(self)

		self.imgLine = np.zeros((h, w, 3), np.uint8)  # 画布
		self.imgBar = np.zeros((h, w, 3), np.uint8)
		self.figure = plt.figure()  # 可选参数,facecolor为背景颜色
		self.canvas = FigureCanvas(self.figure)
		self.DeepList = [0, 0, 0, 0, 0]
		self.NumList = [0, 0, 0, 0, 0]

		self.deep = 0
		self.nowX = multi_thread.g_x
		self.nowY = multi_thread.g_y

		h_o_min = gl.get_value("h_o_min")
		g_start_h_list = gl.get_value("g_start_h_list")

		if h_o_min is not None and g_start_h_list is not None:
			# self.deep = h_o_min - g_start_h_list[0]
			self.deep = h_o_min

		self.__timer = QtCore.QTimer()  # 定时器用于定时刷新
		self.__timer.timeout.connect(self.update_ui)

		self.__timer.start(50)  # ms

	def leftWindow(self, img, sx_list, sy_list, ex_list, ey_list, s_width, e_width, nowX, nowY):
		img[::] = 255  # 画布
		currentPoint = [nowX, nowY]
		currentPoint_move = [None, None]
		currentPoint_zoom = [None, None]
		last_lines = [None, None]  # 保存上一条直线

		sx_list2 = []
		sy_list2 = []
		ex_list2 = []
		ey_list2 = []

		save_line_point_sx_l_list = []
		save_line_point_ex_l_list = []
		save_line_point_sx_r_list = []
		save_line_point_ex_r_list = []
		save_line_point_sy_l_list = []
		save_line_point_ey_l_list = []
		save_line_point_sy_r_list = []
		save_line_point_ey_r_list = []

		save_intersection_xl = []
		save_intersection_xr = []
		save_intersection_yl = []
		save_intersection_yr = []

		"""求出所有点"""
		for i in range(len(sx_list)):
			line_point_s = np.array([sx_list[i], sy_list[i]])
			line_point_e = np.array([ex_list[i], ey_list[i]])

			median_k = (line_point_s[1] - line_point_e[1]) / (line_point_s[0] - line_point_e[0])
			median_b = line_point_s[1] - median_k * line_point_s[0]
			# median_G = np.array([-median_k, 1])
			median_G = np.array([-(line_point_e[1] - line_point_s[1]), (line_point_e[0] - line_point_s[0])])

			# 平移出四个点
			line_point_s_l = line_point_s + s_width[i] * median_G / cv.norm(median_G)
			line_point_s_r = line_point_s - s_width[i] * median_G / cv.norm(median_G)
			line_point_e_l = line_point_e + e_width[i] * median_G / cv.norm(median_G)
			line_point_e_r = line_point_e - e_width[i] * median_G / cv.norm(median_G)

			# 求平移出的直线方程
			kl = (line_point_s_l[1] - line_point_e_l[1]) / (line_point_s_l[0] - line_point_e_l[0])
			bl = line_point_s_l[1] - (kl * line_point_s_l[0])
			kr = (line_point_s_r[1] - line_point_e_r[1]) / (line_point_s_r[0] - line_point_e_r[0])
			br = line_point_s_r[1] - (kr * line_point_s_r[0])

			# 两直线交点
			if i > 0:
				before_line_point_e_l, before_kl, before_bl = last_lines[0]
				before_line_point_e_r, before_kr, before_br = last_lines[1]

				xl = (bl - before_bl) / (before_kl - kl)
				yl = kl * xl + bl
				xr = (br - before_br) / (before_kr - kr)
				yr = kr * xr + br

				# 保存交点坐标
				save_intersection_xl.append(xl)
				save_intersection_yl.append(yl)
				save_intersection_xr.append(xr)
				save_intersection_yr.append(yr)

			# 保存本边界的斜率和终点
			last_lines[0] = (tuple(line_point_e_l), kl, bl)
			last_lines[1] = (tuple(line_point_e_r), kr, br)
			# 保存平移出的4个点坐标
			save_line_point_sx_l_list.append(line_point_s_l[0])
			save_line_point_sx_r_list.append(line_point_s_r[0])
			save_line_point_ex_l_list.append(line_point_e_l[0])
			save_line_point_ex_r_list.append(line_point_e_r[0])

			save_line_point_sy_l_list.append(line_point_s_l[1])
			save_line_point_sy_r_list.append(line_point_s_r[1])
			save_line_point_ey_l_list.append(line_point_e_l[1])
			save_line_point_ey_r_list.append(line_point_e_r[1])

		# 所有点 = 中线坐标 + 平移出的坐标 + 交点坐标
		x_list = (sx_list + ex_list) + \
		         (
				         save_line_point_sx_l_list + save_line_point_sx_r_list + save_line_point_ex_l_list + save_line_point_ex_r_list) + \
		         (save_intersection_xl + save_intersection_xr)
		x_list.append(currentPoint[0])

		y_list = (sy_list + ey_list) + \
		         (
				         save_line_point_sy_l_list + save_line_point_sy_r_list + save_line_point_ey_l_list + save_line_point_ey_r_list) + \
		         (save_intersection_yl + save_intersection_yr)
		y_list.append(currentPoint[1])

		# 平移所有点
		x_min = min(x_list)
		y_min = min(y_list)
		x_max = max(x_list)
		y_max = max(y_list)

		currentPoint_move[0] = currentPoint[0] - x_min
		currentPoint_move[1] = currentPoint[1] - y_min

		x_list[:] = [v - x_min for v in x_list]
		y_list[:] = [v - y_min for v in y_list]

		sx_list2[:] = [v - x_min for v in sx_list]
		sy_list2[:] = [v - y_min for v in sy_list]

		ex_list2[:] = [v - x_min for v in ex_list]
		ey_list2[:] = [v - y_min for v in ey_list]

		save_line_point_sx_l_list[:] = [v - x_min for v in save_line_point_sx_l_list]
		save_line_point_sy_l_list[:] = [v - y_min for v in save_line_point_sy_l_list]

		save_line_point_sx_r_list[:] = [v - x_min for v in save_line_point_sx_r_list]
		save_line_point_sy_r_list[:] = [v - y_min for v in save_line_point_sy_r_list]

		save_line_point_ex_l_list[:] = [v - x_min for v in save_line_point_ex_l_list]
		save_line_point_ey_l_list[:] = [v - y_min for v in save_line_point_ey_l_list]

		save_line_point_ex_r_list[:] = [v - x_min for v in save_line_point_ex_r_list]
		save_line_point_ey_r_list[:] = [v - y_min for v in save_line_point_ey_r_list]

		save_intersection_xl[:] = [v - x_min for v in save_intersection_xl]
		save_intersection_yl[:] = [v - y_min for v in save_intersection_yl]

		save_intersection_xr[:] = [v - x_min for v in save_intersection_xr]
		save_intersection_yr[:] = [v - y_min for v in save_intersection_yr]

		# 找xy的最大差值
		x_delta_max = x_max - x_min
		y_delta_max = y_max - y_min

		# 缩放因子
		global zoom_x, zoom_y
		zoom_x = ((w - 30) / x_delta_max)
		zoom_y = ((h - 30) / y_delta_max)

		# 所有点乘以系数
		currentPoint_zoom[0] = currentPoint_move[0] * zoom_x + delta
		currentPoint_zoom[1] = currentPoint_move[1] * zoom_y + delta

		x_list[:] = [v * zoom_x + delta for v in x_list]
		y_list[:] = [v * zoom_y + delta for v in y_list]

		sx_list2[:] = [v * zoom_x + delta for v in sx_list2]
		sy_list2[:] = [v * zoom_y + delta for v in sy_list2]

		ex_list2[:] = [v * zoom_x + delta for v in ex_list2]
		ey_list2[:] = [v * zoom_y + delta for v in ey_list2]

		save_line_point_sx_l_list[:] = [v * zoom_x + delta for v in save_line_point_sx_l_list]
		save_line_point_sy_l_list[:] = [v * zoom_y + delta for v in save_line_point_sy_l_list]

		save_line_point_ex_l_list[:] = [v * zoom_x + delta for v in save_line_point_ex_l_list]
		save_line_point_ey_l_list[:] = [v * zoom_y + delta for v in save_line_point_ey_l_list]

		save_line_point_sx_r_list[:] = [v * zoom_x + delta for v in save_line_point_sx_r_list]
		save_line_point_sy_r_list[:] = [v * zoom_y + delta for v in save_line_point_sy_r_list]

		save_line_point_ex_r_list[:] = [v * zoom_x + delta for v in save_line_point_ex_r_list]
		save_line_point_ey_r_list[:] = [v * zoom_y + delta for v in save_line_point_ey_r_list]

		save_intersection_xl[:] = [v * zoom_x + delta for v in save_intersection_xl]
		save_intersection_yl[:] = [v * zoom_y + delta for v in save_intersection_yl]

		save_intersection_xr[:] = [v * zoom_x + delta for v in save_intersection_xr]
		save_intersection_yr[:] = [v * zoom_y + delta for v in save_intersection_yr]

		"""判断点的位置"""
		# 每一个直线段偏移出4个点，将这是个点围城一个四边形作为工作区域
		for i in range(len(sx_list)):
			in_flag = isInRect(
				save_line_point_sx_r_list[i], save_line_point_sy_r_list[i],
				save_line_point_sx_l_list[i], save_line_point_sy_l_list[i],
				save_line_point_ex_r_list[i], save_line_point_ey_r_list[i],
				save_line_point_ex_l_list[i], save_line_point_ey_l_list[i],
				currentPoint_zoom[0], currentPoint_zoom[1]
			)
			if in_flag:
				print("当前工作在第%d段" % (i + 1))
			else:
				# print("！！超出工作区域！！")
				pass
		"""画线"""
		# 中线
		for i in range(len(sx_list2)):
			cv.line(img, (int(sx_list2[i]), int(sy_list2[i])), (int(ex_list2[i]), int(ey_list2[i])), (0, 255, 0), 1)

		# 如果交点存在
		if save_intersection_xl:
			# 下面偏移的线
			# 地点到第一个交点
			cv.line(img,
			        (int(save_line_point_sx_l_list[0]), int(save_line_point_sy_l_list[0])),
			        (int(save_intersection_xl[0]), int(save_intersection_yl[0])),
			        (0, 0, 255),
			        2)
			# 交点之间的连线
			for i in range(len(save_intersection_xl) - 1):
				cv.line(img,
				        (int(save_intersection_xl[i]), int(save_intersection_yl[i])),
				        (int(save_intersection_xl[i + 1]), int(save_intersection_yl[i + 1])),
				        (0, 0, 255),
				        2)
			# 交点到最后一个端点
			cv.line(img,
			        (int(save_intersection_xl[-1]), int(save_intersection_yl[-1])),
			        (int(save_line_point_ex_l_list[-1]), int(save_line_point_ey_l_list[-1])),
			        (0, 0, 255),
			        2)

			# 上面偏移的线
			# 地点到第一个交点
			cv.line(img,
			        (int(save_line_point_sx_r_list[0]), int(save_line_point_sy_r_list[0])),
			        (int(save_intersection_xr[0]), int(save_intersection_yr[0])),
			        (0, 0, 255),
			        2)
			# 交点之间的连线
			for i in range(len(save_intersection_xr) - 1):
				cv.line(img,
				        (int(save_intersection_xr[i]), int(save_intersection_yr[i])),
				        (int(save_intersection_xr[i + 1]), int(save_intersection_yr[i + 1])),
				        (0, 0, 255),
				        2)
			# 交点到最后一个端点
			cv.line(img,
			        (int(save_intersection_xr[-1]), int(save_intersection_yr[-1])),
			        (int(save_line_point_ex_r_list[-1]), int(save_line_point_ey_r_list[-1])),
			        (0, 0, 255),
			        2)

		# 如果交点不存在
		if not save_intersection_xl:
			cv.line(img,
			        (int(save_line_point_sx_l_list[0]), int(save_line_point_sy_l_list[0])),
			        (int(save_line_point_ex_l_list[-1]), int(save_line_point_ey_l_list[-1])),
			        (0, 0, 255),
			        2)

			cv.line(img,
			        (int(save_line_point_sx_r_list[0]), int(save_line_point_sy_r_list[0])),
			        (int(save_line_point_ex_r_list[-1]), int(save_line_point_ey_r_list[-1])),
			        (0, 0, 255),
			        2)

		# 交点
		# for i in range(len(save_intersection_xl)):
		#     cv.circle(img, (int(save_intersection_xl[i]), int(save_intersection_yl[i])), 3, (255, 0, 0), -1)  # 上
		#     cv.circle(img, (int(save_intersection_xr[i]), int(save_intersection_yr[i])), 3, (255, 0, 0), -1)

		# 闭合首
		cv.line(img,
		        (int(save_line_point_sx_l_list[0]), int(save_line_point_sy_l_list[0])),
		        (int(save_line_point_sx_r_list[0]), int(save_line_point_sy_r_list[0])),
		        (0, 0, 255),
		        2)

		# 闭合尾
		cv.line(img,
		        (int(save_line_point_ex_l_list[-1]), int(save_line_point_ey_l_list[-1])),
		        (int(save_line_point_ex_r_list[-1]), int(save_line_point_ey_r_list[-1])),
		        (0, 0, 255),
		        2)

		gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
		ret, binary = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)  # 转为二值图
		_, contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

		# 画出轮廓线
		# draw_img = img.copy()
		# res = cv.drawContours(draw_img, contours, 1, (0, 255, 0), 2)
		# cv.imshow('res', res)

		# show_img("l", img)

		currentPoint_zoom = (
			int(currentPoint_zoom[0]),
			int(currentPoint_zoom[1])
		)

		cv.circle(img, currentPoint_zoom, 5, [0, 0, 255], -1)

		dist = cv.pointPolygonTest(contours[1], currentPoint_zoom, False)
		# print("dist:", dist)
		gl.set_value("dist", dist)

		QtImgLine = QImage(cv.cvtColor(img, cv.COLOR_BGR2RGB).data,
		                   img.shape[1],
		                   img.shape[0],
		                   img.shape[1] * 3,  # 每行的字节数, 彩图*3
		                   QImage.Format_RGB888)

		pixmapL = QPixmap(QtImgLine)

		self.leftLabel.setPixmap(pixmapL)
		self.leftLabel.setScaledContents(True)

	def rightWindow(self, img, deep):
		img[::] = 255  # 设置画布颜色

		if len(self.NumList) >= 5:  # 最多显示5条柱状图
			self.DeepList.pop(0)
			self.NumList.pop(0)

		self.DeepList.append(deep)
		self.NumList.append(' ')

		self.DeepList = list(map(float, self.DeepList))

		# 将x,y轴转化为矩阵式
		x = np.arange(len(self.NumList)) + 1
		y = np.array(self.DeepList)

		colors = ["g" if i > 0 else "r" for i in self.DeepList]
		plt.clf()  # 清空画布
		plt.bar(range(len(self.NumList)), self.DeepList, tick_label=self.NumList, color=colors, width=0.5)

		# 在柱体上显示数据
		for a, b in zip(x, y):
			plt.text(a - 1, b, '%.4f' % b, ha='center', va='bottom')

		# 画图
		self.canvas.draw()

		img = np.array(self.canvas.renderer.buffer_rgba())

		QtImgBar = QImage(img.data,
		                  img.shape[1],
		                  img.shape[0],
		                  img.shape[1] * 4,
		                  QImage.Format_RGBA8888)
		pixmapR = QPixmap(QtImgBar)

		self.rightLabel.setPixmap(pixmapR)
		self.rightLabel.setScaledContents(True)  # 让图片自适应label大小

	def paintEvent(self, e):
		x = self.groupBox_3.x()
		y = self.groupBox_3.y()

		h_border_warning = self.border_warning.height()
		w_border_warning = self.border_warning.width()

		h_gps_warning = self.gps_warning.height()
		w_gps_warning = self.gps_warning.width()

		x_border_warning = x + w_border_warning / 2
		y_border_warning = y + h_border_warning / 2 - 10
		# print("border_warning", x_border_warning, y_border_warning)
		x_gps_warning = x + w_gps_warning / 2
		y_gps_warning = y + h_gps_warning / 2 + 100
		# print("h_gps_warning", x_gps_warning, y_gps_warning)

		qp = QPainter()
		qp.begin(self)
		"""GPS信号指示灯"""
		gps_stable_flag = gl.get_value("gps_stable_flag")
		if gps_stable_flag is not None:
			if gps_stable_flag:
				gps_warning_led(qp, Qt.green, x_gps_warning, y_gps_warning)
			elif not gps_stable_flag:
				gps_warning_led(qp, Qt.red, x_gps_warning, y_gps_warning)
			else:
				gps_warning_led(qp, Qt.yellow, x_gps_warning, y_gps_warning)

			"""边界信号指示灯"""
			dist = gl.get_value("dist")
			if dist is not None:
				if dist == -1:
					border_warning_led(qp, Qt.red, x_border_warning, y_border_warning)
				elif dist == 1 or dist == 0:
					border_warning_led(qp, Qt.green, x_border_warning, y_border_warning)
				else:
					border_warning_led(qp, Qt.yellow, x_border_warning, y_border_warning)
		qp.end()
		# 刷新
		self.setUpdatesEnabled(True)
		self.update()

	def update_ui(self):
		g_ui_threadLock.acquire()

		h_o_min_flag = gl.get_value("h_o_min_flag")
		# TODO 测试
		h_o_min_flag = True
		self.deep = random.randint(-100, 300)

		if h_o_min_flag:
			# 清空标志位
			h_o_min_flag = gl.set_value("h_o_min_flag", False)

			# 显示挖掘深度
			self.now_deep.setText(str(self.deep) + "米")
			self.rightWindow(self.imgBar, self.deep)
		else:
			pass
			# print("working...")
		g_start_x_list = gl.get_value('g_start_x_list')
		g_start_y_list = gl.get_value('g_start_y_list')
		g_start_h_list = gl.get_value('g_start_h_list')
		g_start_w_list = gl.get_value('g_start_w_list')
		g_end_x_list = gl.get_value('g_end_x_list')
		g_end_y_list = gl.get_value('g_end_y_list')
		g_end_h_list = gl.get_value('g_end_h_list')
		g_end_w_list = gl.get_value('g_end_w_list')

		# TODO:测试数据
		# current_x = self.nowX
		# current_y = self.nowY
		current_x = random.randint(1, 300)
		current_y = random.randint(1, 300)
		self.leftWindow(self.imgLine, g_start_x_list, g_start_y_list, g_end_x_list, g_end_y_list,
		                g_start_w_list,
		                g_end_w_list,
		                int(current_x),
		                int(current_y),
		                )
		# 显示挖掘机ID
		digger_id = gl.get_value("diggerId")
		self.diggerID.setText(str(digger_id))
		# 显示当前坐标
		global x_min, y_min
		self.nowXY.setText("(%.3f, %.3f)"
		                   % ((current_x - x_min) * zoom_x + delta, (current_y - y_min) * zoom_x + delta))

		g_ui_threadLock.release()  # ????????????????????????

		date = QDateTime.currentDateTime()
		current_time = date.toString("yyyy-MM-dd hh:mm dddd")
		self.time.setText(current_time)


if __name__ == "__main__":
	gl.gl_init()

	# 使用Daemon(True)把所有的子线程都变成了主线程的守护线程，因此当主进程结束后，子线程也会随之结束
	gps_thread = threading.Thread(target=multi_thread.thread_gps_func, daemon=False)
	_4g_thread = threading.Thread(target=multi_thread.thread_4g_func, daemon=False)
	# gyro_thread = threading.Thread(target=multi_thread.thread_gyro2_func, daemon=False)
	# gyro_3_thread = threading.Thread(target=multi_thread.thread_gyro3_func, daemon=False)
	# g_laser1_thread = threading.Thread(target=multi_thread.thread_laser1_func, daemon=False)
	# g_laser2_thread = threading.Thread(target=multi_thread.thread_laser2_func, daemon=False)
	# g_laser3_thread = threading.Thread(target=multi_thread.thread_laser3_func, daemon=False)
	# calculate_thread = threading.Thread(target=calculate.altitude_calculate_func, daemon=False)

	gps_thread.start()  # 启动线程
	# gyro_thread.start()
	# gyro_3_thread.start()
	# g_laser1_thread.start()
	# g_laser2_thread.start()
	# g_laser3_thread.start()
	# sleep(1)
	# calculate_thread.start()
	_4g_thread.start()

	app = QApplication(sys.argv)
	mainWindow = MyWindows()

	while True:
		received_flag = gl.get_value("received_flag")
		if received_flag:
			# 清空接受完成标志位
			received_flag = False
			gl.set_value("received_flag", received_flag)

			mainWindow = MyWindows()
			mainWindow.showFullScreen()  # 窗口全屏显示
			mainWindow.show()
			sys.exit(app.exec_())
