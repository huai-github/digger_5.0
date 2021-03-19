#!/usr/bin/python3
# coding = utf-8

import datetime
import time
from serial_port import SerialPortCommunication
import globalvar as gl
from globalvar import my_lock


def gyroDataAnalysis(gyro_rec_buf, addr):
	RollH = gyro_rec_buf[3]
	RollL = gyro_rec_buf[4]
	PitchH = gyro_rec_buf[5]
	PitchL = gyro_rec_buf[6]
	if gyro_rec_buf[0] == addr and gyro_rec_buf[1] == 0x03:
		roll = int(((RollH << 8) | RollL)) / 32768 * 180
		pitch = int(((PitchH << 8) | PitchL)) / 32768 * 180
		if roll > 180:
			roll = (roll - 360)
		if pitch > 180:
			pitch = (pitch - 360)
		roll = round(roll, 2)
		pitch = round(pitch, 2)

		if roll is not None and pitch is not None:
			# time.sleep(0.1)
			return roll, pitch
		else:
			return


def bus485ThreadFunc():
	# BUS_COM = "com7"
	BUS_COM = "com5"
	GyroRecBufLen = (11 * 3)
	gyroChassisAddr = 0x50
	gyroBigArmAddr = 0x51
	gyroLittleArmAddr = 0x52

	bus485 = SerialPortCommunication(BUS_COM, 115200, 0.005)
	gyroChassisReadCmd = [gyroChassisAddr, 0x03, 0x00, 0x3d, 0x00, 0x03, 0x99, 0x86]
	gyroBigArmReadCmd = [gyroBigArmAddr, 0x03, 0x00, 0x3d, 0x00, 0x03, 0x98, 0x57]
	gyroLittleReadCmd = [gyroLittleArmAddr, 0x03, 0x00, 0x3d, 0x00, 0x03, 0x98, 0x64]

	""" 准备工作 """
	while True:
		gyroChassisAngle = []
		gyroBigArmAngle = []
		gyroLittleArmAngle = []

		chassis_data_ready = False
		big_data_ready = False
		little_data_ready = False

		# 全局变量初始化
		_485_data_valid_flg = False
		roll_2_di_pan = 0
		pitch_2_di_pan = 0
		roll_2_da_bi = 0
		roll_2_xiao_bi = 0

		chassisLen = bus485.send_data(gyroChassisReadCmd)
		time.sleep(0.001)
		if chassisLen == len(gyroChassisReadCmd):
			gyroChassisRecBuf = bus485.read_size(GyroRecBufLen)
			if gyroChassisRecBuf != b'':
				gyroChassisAngle = gyroDataAnalysis(gyroChassisRecBuf, gyroChassisAddr)
				chassis_data_ready = True
				roll_2_di_pan = gyroChassisAngle[0]
				pitch_2_di_pan = gyroChassisAngle[1]
			else:
				print("准备流程--地盘--接收数组为空\n")
		else:
			print("准备流程--地盘--地址发送失败\n")
		time.sleep(0.001)

		bigArmLen = bus485.send_data(gyroBigArmReadCmd)
		time.sleep(0.001)
		if bigArmLen == len(gyroBigArmReadCmd):
			gyroBigArmRecBuf = bus485.read_size(GyroRecBufLen)
			# TODO：判断条件
			if gyroBigArmRecBuf != b'':
				gyroBigArmAngle = gyroDataAnalysis(gyroBigArmRecBuf, gyroBigArmAddr)
				big_data_ready = True
				roll_2_da_bi = gyroBigArmAngle[0]
			else:
				print("准备流程--大臂--接收数组为空\n")
		else:
			print("准备流程--大臂--地址发送失败\n")
		time.sleep(0.001)

		littleArmLen = bus485.send_data(gyroLittleReadCmd)
		time.sleep(0.001)
		if littleArmLen == len(gyroLittleReadCmd):
			gyroLittleArmRecBuf = bus485.read_size(GyroRecBufLen)
			if gyroLittleArmRecBuf != b'':
				gyroLittleArmAngle = gyroDataAnalysis(gyroLittleArmRecBuf, gyroLittleArmAddr)
				little_data_ready = True
				roll_2_xiao_bi = gyroLittleArmAngle[0]
			else:
				print("准备流程--小臂--接收数组为空\n")
		else:
			print("准备流程--小臂--地址发送失败\n")

		# print("==============================485准备：", chassis_data_ready, big_data_ready, little_data_ready)
		if chassis_data_ready and big_data_ready and little_data_ready:
			_485_data_valid_flg = True
			# 设置全局变量
			with open("lock_log.txt", "a") as file:
				file.write("485线程--calu_485--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
			my_lock.Calculator485Lock.acquire()
			with open("lock_log.txt", "a") as file:
				file.write("485线程--calu_485--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
			gl.set_value("roll_2_di_pan", roll_2_di_pan)
			gl.set_value("pitch_2_di_pan", pitch_2_di_pan)
			gl.set_value("roll_2_da_bi", roll_2_da_bi)
			gl.set_value("roll_2_xiao_bi", roll_2_xiao_bi)
			gl.set_value("_485_data_valid_flg", _485_data_valid_flg)
			my_lock.Calculator485Lock.release()
			with open("lock_log.txt", "a") as file:
				file.write("485线程--calu_485--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
			break
		else:
			print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCgyroChassisAngle:%s\n" % gyroChassisAngle)
			print("BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBgyroBigArmAngle:%s\n" % gyroBigArmAngle)
			print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLgyroLittleArmAngle:%s\n" % gyroLittleArmAngle)

		time.sleep(0.1)

	""" 正常流程 """
	while True:
		roll_2_di_pan = 0
		pitch_2_di_pan = 0
		roll_2_da_bi = 0
		roll_2_xiao_bi = 0

		gyroChassisAngle = []
		gyroBigArmAngle = []
		gyroLittleArmAngle = []
		time.sleep(0.001)
		if bus485.com.is_open:
			chassisLen = bus485.send_data(gyroChassisReadCmd)
			time.sleep(0.001)
			if chassisLen == len(gyroChassisReadCmd):
				gyroChassisRecBuf = bus485.read_size(GyroRecBufLen)
				if gyroChassisRecBuf != b'':
					gyroChassisAngle = gyroDataAnalysis(gyroChassisRecBuf, gyroChassisAddr)
					# print("===========================地盘角度：", gyroChassisAngle)
					gyroLedChassis = True
					roll_2_di_pan = gyroChassisAngle[0]
					pitch_2_di_pan = gyroChassisAngle[1]
				else:
					gyroLedChassis = False
					print("工作流程--底盘--接收数组为空\n")
			else:
				gyroLedChassis = False
				print("工作流程--底盘--发送失败\n")
			time.sleep(0.001)

			bigArmLen = bus485.send_data(gyroBigArmReadCmd)
			time.sleep(0.001)
			if bigArmLen == len(gyroBigArmReadCmd):
				gyroBigArmRecBuf = bus485.read_size(GyroRecBufLen)
				if gyroBigArmRecBuf != b'':
					gyroBigArmAngle = gyroDataAnalysis(gyroBigArmRecBuf, gyroBigArmAddr)
					# print("===========================大臂角度：", gyroBigArmAngle)
					gyroBigLed = True
					roll_2_da_bi = gyroBigArmAngle[0]
				else:
					gyroBigLed = False
					print("工作流程--大臂--接收数组为空\n")
			else:
				gyroBigLed = False
				# gl.set_value("gyroBigLed", False)
				print("工作流程--大臂--发送失败\n")
			time.sleep(0.001)

			littleArmLen = bus485.send_data(gyroLittleReadCmd)
			time.sleep(0.001)
			if littleArmLen == len(gyroLittleReadCmd):
				gyroLittleArmRecBuf = bus485.read_size(GyroRecBufLen)
				if gyroLittleArmRecBuf != b'':
					gyroLittleArmAngle = gyroDataAnalysis(gyroLittleArmRecBuf, gyroLittleArmAddr)
					# print("===========================小臂角度：", gyroLittleArmAngle)
					gyroLittleLed = True
					roll_2_xiao_bi = gyroLittleArmAngle[0]
				else:
					gyroLittleLed = False
					print("工作流程--小臂--接收数组为空\n")
			else:
				gyroLittleLed = False
				print("工作流程--小臂--发送失败\n")

			if gyroChassisAngle and gyroBigArmAngle and gyroLittleArmAngle:
				# 设置全局变量
				with open("lock_log.txt", "a") as file:
					file.write("485线程--calu_485--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
				my_lock.Calculator485Lock.acquire()
				with open("lock_log.txt", "a") as file:
					file.write("485线程--calu_485--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
				gl.set_value("roll_2_di_pan", roll_2_di_pan)
				gl.set_value("pitch_2_di_pan", pitch_2_di_pan)
				gl.set_value("roll_2_da_bi", roll_2_da_bi)
				gl.set_value("roll_2_xiao_bi", roll_2_xiao_bi)
				my_lock.Calculator485Lock.release()
				with open("lock_log.txt", "a") as file:
					file.write("485线程--calu_485--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		else:
			gyroLedChassis = False
			gyroBigLed = False
			gyroLittleLed = False

		with open("lock_log.txt", "a") as file:
			file.write("485线程--gyrolec--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.gyroLedLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("485线程--gyrolec--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gl.set_value("gyroLedChassis", gyroLedChassis)
		gl.set_value("gyroBigLed", gyroBigLed)
		gl.set_value("gyroLittleLed", gyroLittleLed)
		my_lock.gyroLedLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("485线程--gyrolec--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		time.sleep(0.01)
		print("！！！！！485线程！！！！！%s\n" % datetime.datetime.now().strftime('%H:%M:%S.%f'))

