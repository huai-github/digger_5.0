import datetime
import threading
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
			time.sleep(0.1)
			return roll, pitch
		else:
			return


def bus485ThreadFunc():
	BUS_COM = "com7"
	GyroRecBufLen = (11 * 3)
	gyroChassisAddr = 0x50
	gyroBigArmAddr = 0x51
	gyroLittleArmAddr = 0x52

	bus485 = SerialPortCommunication(BUS_COM, 115200, 0.005)
	gyroChassisReadCmd = [gyroChassisAddr, 0x03, 0x00, 0x3d, 0x00, 0x03, 0x99, 0x86]
	gyroBigArmReadCmd = [gyroBigArmAddr, 0x03, 0x00, 0x3d, 0x00, 0x03, 0x98, 0x57]
	gyroLittleReadCmd = [gyroLittleArmAddr, 0x03, 0x00, 0x3d, 0x00, 0x03, 0x98, 0x64]

	while True:
		"""底盘"""
		time.sleep(0.001)
		chassisLen = bus485.send_data(gyroChassisReadCmd)
		time.sleep(0.001)
		if chassisLen is not None:
			gyroChassisRecBuf = bus485.read_size(GyroRecBufLen)
			if gyroChassisRecBuf != b'':
				gyroChassisAngle = gyroDataAnalysis(gyroChassisRecBuf, gyroChassisAddr)
				#print("gyroChassisAngle:", gyroChassisAngle)
			else:
				print("\r\n!!底盘陀螺仪--接受数据失败!! \r\n")
				print("--ERROR-- gyroChassisRecBuf:", gyroChassisRecBuf)
				break
		else:
			print("\r\n!!底盘陀螺仪--地址发送失败!! \r\n")
			break

		time.sleep(0.001)
		"""大臂"""
		bigArmLen = bus485.send_data(gyroBigArmReadCmd)
		time.sleep(0.001)
		if bigArmLen is not None:
			gyroBigArmRecBuf = bus485.read_size(GyroRecBufLen)
			# print("gyroBigArmRecBuf:", gyroBigArmRecBuf)
			if gyroBigArmRecBuf != b'':
				gyroBigArmAngle = gyroDataAnalysis(gyroBigArmRecBuf, gyroBigArmAddr)
				#print("gyroBigArmAngle:", gyroBigArmAngle)
			else:
				print("\r\n!!大臂陀螺仪--数据接受失败!! \r\n")
				print("--ERROR-- gyroBigArmRecBuf:", gyroBigArmRecBuf)
				break
		else:
			print("\r\n!!大臂陀螺仪--地址发送失败!! \r\n")
			break

		"""小臂"""
		time.sleep(0.001)
		littleArmLen = bus485.send_data(gyroLittleReadCmd)
		time.sleep(0.001)
		if littleArmLen is not None:
			gyroLittleArmRecBuf = bus485.read_size(GyroRecBufLen)
			# print("gyroLittleArmRecBuf:", gyroLittleArmRecBuf)
			if gyroLittleArmRecBuf != b'':
				gyroLittleArmAngle = gyroDataAnalysis(gyroLittleArmRecBuf, gyroLittleArmAddr)
				#print("gyroLittleArmAngle:", gyroLittleArmAngle)
				# gl.set_value()
			else:
				print("\r\n!!小臂陀螺仪--数据接受失败!! \r\n")
				print("--ERROR-- gyroLittleArmRecBuf:", gyroLittleArmRecBuf)
				break
		else:
			print("\r\n!!小臂陀螺仪--地址发送失败!! \r\n")
			break

		gl.set_value("roll_2_di_pan", gyroChassisAngle[0])
		gl.set_value("pitch_2_di_pan", gyroChassisAngle[1])
		gl.set_value("roll_2_da_bi", gyroBigArmAngle[0])
		gl.set_value("pitch_2_da_bi", gyroBigArmAngle[1])
		gl.set_value("roll_2_xiao_bi", gyroLittleArmAngle[0])
		gl.set_value("pitch_2_xiao_bi", gyroLittleArmAngle[1])


if __name__ == '__main__':
	gl.gl_init()
	bus485ThreadFunc()