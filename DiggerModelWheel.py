# 挖掘机转盘模型，求大臂低端坐标
import numpy as np


def DiggerModelWheel():
	# 挖掘机结构参数
	HC2T = 1591 + 155 + 319  # %天线到转盘底部1607顶部到车棚底，319黄色底座厚度，130横杆到天线的高度

	# a点坐标
	x_a = 40
	y_a = 800  # a到转盘中心的距离
	z_a = - HC2T + (337 + 185)  # a到底部的距离是337+185

	# 圆盘中心坐标
	x_q = 0
	y_q = 0
	z_q = -HC2T

	# rst = concat([[x_a, y_a, z_a], [x_q, y_q, z_q]])
	rst = np.array([
		[x_a, y_a, z_a],
		[x_q, y_q, z_q]
	])

	return rst
