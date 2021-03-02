from serial_port import SerialPortCommunication


class Gyro2(object):
	def __init__(self, com):
		self.roll = 0
		self.pitch = 0
		self.GYRO_COM = com
		self.GYRO_REC_BUF_LEN = (11 * 3)
		self.com_gyro = SerialPortCommunication(self.GYRO_COM, 115200, 0.5)

	def get_angle(self):

		gyro_rec_buf = self.com_gyro.read_size(self.GYRO_REC_BUF_LEN)
		if gyro_rec_buf:
			RollH = gyro_rec_buf[3]
			RollL = gyro_rec_buf[4]
			PitchH = gyro_rec_buf[5]
			PitchL = gyro_rec_buf[6]

			if gyro_rec_buf[0] == 0x50 and gyro_rec_buf[1] == 0x03:
				self.roll = int(((RollH << 8) | RollL)) / 32768 * 180
				self.pitch = int(((PitchH << 8) | PitchL)) / 32768 * 180

				self.roll = round(self.roll, 2)  # 保存2位小数
				self.pitch = round(self.pitch, 2)
				return self.roll, self.pitch
		else:
			self.roll = 0
			self.pitch = 0
			print("Big arm  gyro data is null")
			return self.roll, self.pitch

class Gyro3(object):
	def __init__(self, com):
		self.roll = 0
		self.pitch = 0
		self.yaw = 0
		self.GYRO_COM = com
		self.GYRO_REC_BUF_LEN = (11 * 4)
		self.com_gyro = SerialPortCommunication(self.GYRO_COM, 9600, 0.5)

	def get_angle(self):
		gyro_rec_buf = self.com_gyro.read_size(self.GYRO_REC_BUF_LEN)
		target_index = gyro_rec_buf.find(0x53)  # 数据头2角度输出
		if target_index != (-1):
			if gyro_rec_buf[target_index - 1] == 0x55:  # 数据头1
				data = gyro_rec_buf[(target_index - 1):(target_index + 10)]
				self.roll = int(((data[3] << 8) | data[2])) / 32768 * 180
				self.pitch = int(((data[5] << 8) | data[4])) / 32768 * 180
				self.yaw = int(((data[7] << 8) | data[6])) / 32768 * 180
				print("roll:", self.roll)
				print("pitch:", self.pitch)
				print("yaw:", self.yaw)
			else:
				print("header 1 error")
				return -1
		else:
			print("header 2 error")
			return -1
