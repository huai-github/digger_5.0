#!/usr/bin/python3
# coding = utf-8

import sys
import threading
from time import sleep
import datetime
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QBrush, QImage, QPixmap, QPainter
from PyQt5.QtWidgets import QApplication, QWidget

import calculate_main
import digger_ui
import multi_thread
import globalvar as gl
import time
import WinMaintn
import runCalibrationUi
import _485bus
from globalvar import my_lock


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
		with open("lock_log.txt", "a") as file:
			file.write("主线程--win_ui--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.WinUiLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--win_ui--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		lftWinImg = gl.get_value("lftWinImg")
		RitWinImg = gl.get_value("RitWinImg")
		lftWinImgFlg = gl.get_value("lftWinImgFlg")
		RitWinImgFlg = gl.get_value("RitWinImgFlg")
		# current_work_high = gl.get_value("current_work_high")  # 当前点的施工高度
		dist = gl.get_value("dist")
		deep = gl.get_value("deep")
		my_lock.WinUiLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--win_ui--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("主线程--gps_ui--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.gpsStableLedLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--gps_ui--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gps_stable_flag = gl.get_value("gps_stable_flag")  # gpsUI
		my_lock.gpsStableLedLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--gps_ui--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("主线程--gps_led--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.gpsLedLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--gps_led--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gps_is_open_led = gl.get_value("gps_is_open_led")  # gps串口是否打开
		my_lock.gpsLedLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--gps_led--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("主线程--laser_led--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.laserLedLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--laser_led--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		laserLed = gl.get_value("laserLed")  # laserUI
		my_lock.laserLedLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--laser_led--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("主线程--gyro_led--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.gyroLedLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--gyro_led--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gyroLedChassis = gl.get_value("gyroLedChassis")  # 485UI
		gyroBigLed = gl.get_value("gyroBigLed")  # 485UI
		gyroLittleLed = gl.get_value("gyroLittleLed")  # 485UI
		my_lock.gyroLedLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("主线程--gyro_led--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		qp = QPainter()
		qp.begin(self)
		"""GPS信号指示灯"""
		if gps_stable_flag:
			self.gps_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:green")
		else:
			self.gps_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:red")

		"""边界信号指示灯"""
		if dist == -1:
			self.edge_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:red")
		elif dist == 1 or dist == 0:
			self.edge_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:green")
		else:
			self.edge_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:yellow")

		""" gps串口是否打开 """
		if gps_is_open_led:
			pass
		else:
			pass

		""" 深度指示灯 """
		if deep > 0:
			self.deep_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:green")
		else:
			self.deep_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:red")

		""" 激光指示灯 """
		if laserLed:
			self.laser_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:green")
		else:
			self.laser_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:red")

		""" 陀螺仪指示灯 """
		if gyroLedChassis:
			self.gyro_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:green")
		else:
			self.gyro_led.setStyleSheet("min-width:40px;min-height:40px;max-width:40px;max-height:40px;border-radius:20px;border:1pxsolidblack;background:red")

		"""维护界面"""
		# 维护左窗口
		if lftWinImgFlg:
			QtImgLine = QImage(cv.cvtColor(lftWinImg, cv.COLOR_BGR2RGB).data,
			                   lftWinImg.shape[1],
			                   lftWinImg.shape[0],
			                   lftWinImg.shape[1] * 3,  # 每行的字节数, 彩图*3
			                   QImage.Format_RGB888)
			pixmapL = QPixmap(QtImgLine)
			self.leftLabel.setPixmap(pixmapL)
			self.leftLabel.setScaledContents(True)

		# 维护右窗口
		if RitWinImgFlg:
			QtImgLine = QImage(cv.cvtColor(RitWinImg, cv.COLOR_BGR2RGB).data,
			                   RitWinImg.shape[1],
			                   RitWinImg.shape[0],
			                   RitWinImg.shape[1] * 3,  # 每行的字节数, 彩图*3
			                   QImage.Format_RGB888)
			pixmapL = QPixmap(QtImgLine)
			self.rightLabel.setPixmap(pixmapL)
			self.rightLabel.setScaledContents(True)

		# """显示挖掘机ID"""
		# self.diggerID.setText(str(digger_id))

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

	gps_thread.start()  # 启动线程
	_485_thread.start()
	g_laser_dou_thread.start()
	_4g_thread.start()

	calculate_thread.start()
	WinMaintn_thread.start()
	sleep(1)

	app = QApplication(sys.argv)
	mainWindow = MyWindows()

	while True:
		time.sleep(0.01)
		run = gl.get_value("main_win_data_valid_flg")

		if run:
			mainWindow = MyWindows()
			mainWindow.setWindowState(Qt.WindowMaximized)
			mainWindow.showFullScreen()  # 窗口全屏显示
			mainWindow.showMaximized()
			mainWindow.show()
			sys.exit(app.exec_())
