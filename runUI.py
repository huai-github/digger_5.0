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
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton

import calculate_main
import digger_ui
import multi_thread
import globalvar as gl
import time
import WinMaintn
import datetime
import runCalibrationUi
import _485bus

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


def gps_warning_led(qp, color, x, y):
	qp.setPen(color)
	brush = QBrush(Qt.SolidPattern)
	qp.setBrush(brush)
	qp.setBrush(color)
	qp.drawEllipse(int(x), int(y), 20, 20)


def border_warning_led(qp, color, x, y):
	qp.setPen(color)
	brush = QBrush(Qt.SolidPattern)
	qp.setBrush(brush)
	qp.setBrush(color)
	qp.drawEllipse(int(x), int(y), 20, 20)


class MyWindows(QWidget, digger_ui.Ui_Digger):
	def __init__(self):
		super().__init__()
		self.setupUi(self)

		self.imgLine = np.zeros((h, w, 3), np.uint8)  # 画布
		self.imgBar = np.zeros((h, w, 3), np.uint8)
		self.figure = plt.figure()  # 可选参数, facecolor为背景颜色
		self.canvas = FigureCanvas(self.figure)
		self.DeepList = [0, 0, 0, 0, 0]
		self.NumList = [0, 0, 0, 0, 0]

		self.deep = 0
		self.nowX = multi_thread.g_x
		self.nowY = multi_thread.g_y

		# 校准按钮
		self.calibration_button.clicked.connect(self.calibrationBtnFunc)

	def calibrationBtnFunc(self):
		self.calibration_text.setText("已按下校准按钮。。。")
		self.hide()  # 隐藏此窗口
		self.calibrationUi = runCalibrationUi.CalibrationUi()
		# self.calibrationUi.showFullScreen()  # 窗口全屏显示
		# self.calibrationUi.showMaximized()
		self.calibrationUi.show()  # 经第二个窗口显示出来

	def paintEvent(self, e):
		# time_now = datetime.datetime.now().strftime('%H:%M:%S.%f')
		# print("1111111111111111111111111111111111111111111111111111111", time_now)

		x = self.groupBox_3.x()
		y = self.groupBox_3.y()

		h_border_warning = self.border_warning.height()
		w_border_warning = self.border_warning.width()

		x_border_warning = x + w_border_warning / 2 + 30
		y_border_warning = y + h_border_warning / 2

		x_gps_warning = x_border_warning
		y_gps_warning = y_border_warning + self.border_warning.height()

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
				# sys.exit()
				elif dist == 1 or dist == 0:
					border_warning_led(qp, Qt.green, x_border_warning, y_border_warning)
				else:
					border_warning_led(qp, Qt.yellow, x_border_warning, y_border_warning)

		"""维护界面"""
		# 维护左窗口
		lftWinImg = gl.get_value("lftWinImg")
		if gl.get_value("lftWinImgFlg"):
			QtImgLine = QImage(cv.cvtColor(lftWinImg, cv.COLOR_BGR2RGB).data,
			                   lftWinImg.shape[1],
			                   lftWinImg.shape[0],
			                   lftWinImg.shape[1] * 3,  # 每行的字节数, 彩图*3
			                   QImage.Format_RGB888)
			pixmapL = QPixmap(QtImgLine)
			self.leftLabel.setPixmap(pixmapL)
			self.leftLabel.setScaledContents(True)

		# 维护右窗口
		RitWinImg = gl.get_value("RitWinImg")
		if gl.get_value("RitWinImgFlg"):
			QtImgLine = QImage(cv.cvtColor(RitWinImg, cv.COLOR_BGR2RGB).data,
			                   RitWinImg.shape[1],
			                   RitWinImg.shape[0],
			                   RitWinImg.shape[1] * 3,  # 每行的字节数, 彩图*3
			                   QImage.Format_RGB888)
			pixmapL = QPixmap(QtImgLine)
			self.rightLabel.setPixmap(pixmapL)
			self.rightLabel.setScaledContents(True)

		"""显示挖掘机ID"""
		digger_id = gl.get_value("diggerId")
		self.diggerID.setText(str(digger_id))

		"""显示当前坐标"""
		current_x = gl.get_value('o_x') / 1000
		current_y = gl.get_value('o_y') / 1000
		self.nowXY.setText("(%.3f, %.3f)" % (current_x, current_y))

		"""显示当前深度"""
		o_h = gl.get_value("o_h")
		g_start_h_list = gl.get_value("g_start_h_list")
		self.deep = o_h / 1000 - g_start_h_list[0]
		deepShow = round(self.deep, 3)
		self.now_deep.setText(str(deepShow) + "米")

		"""显示时间"""
		date = QDateTime.currentDateTime()
		current_time = date.toString("yyyy-MM-dd hh:mm dddd")
		self.time.setText(current_time)

		qp.end()
		# 刷新
		self.setUpdatesEnabled(True)
		self.update()
		# time_now = datetime.datetime.now().strftime('%H:%M:%S.%f')
		# print("222222222222222222222222222222222222222222222222222222222", time_now)


if __name__ == "__main__":
	gl.gl_init()
	# 使用Daemon(True)把所有的子线程都变成了主线程的守护线程，因此当主进程结束后，子线程也会随之结束
	gps_thread = threading.Thread(target=multi_thread.thread_gps_func, daemon=True)
	_4g_thread = threading.Thread(target=multi_thread.thread_4g_func, daemon=True)
	_485_thread = threading.Thread(target=_485bus.bus485ThreadFunc, daemon=True)
	g_laser_dou_thread = threading.Thread(target=multi_thread.thread_laser_dou_func, daemon=True)
	calculate_thread = threading.Thread(target=calculate_main.thread_calculate_func, daemon=True)
	WinMaintn_thread = threading.Thread(target=WinMaintn.WinMaintnFun, daemon=True)

	gps_thread.start()  # 启动线程11
	_485_thread.start()
	g_laser_dou_thread.start()
	_4g_thread.start()
	sleep(10)
	calculate_thread.start()
	sleep(3)
	WinMaintn_thread.start()
	sleep(1)









	app = QApplication(sys.argv)
	mainWindow = MyWindows()

	# f = open("out.txt", "w")
	while True:
		# time.sleep(1)
		taskAnalysisFlg = gl.get_value("taskAnalysisFlg")
		if taskAnalysisFlg:
			# 清空接受完成标志位
			taskAnalysisFlg = False
			gl.set_value("taskAnalysisFlg", taskAnalysisFlg)

			mainWindow = MyWindows()
			mainWindow.setWindowState(Qt.WindowMaximized)
			# mainWindow.showFullScreen()  # 窗口全屏显示
			# mainWindow.showMaximized()
			mainWindow.show()
			sys.exit(app.exec_())
