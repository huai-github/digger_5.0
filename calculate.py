import globalvar as gl


da_bi_total = 0
xiao_bi_total = 0
dou_total = 0


def parameter_config():
	if gl.get_value("calibration_on_button_flag"):
		# 清空标志位
		gl.set_value("calibration_on_button_flag", False)
		# 臂缩到做最短时，可以知道臂的长度，此时臂长-激光长度 == 固定长度（初始化的值）
		da_bi_config = da_bi_total - gl.get_value("da_bi_config")
		xiao_bi_config = xiao_bi_total - gl.get_value("xiao_bi_config")
		dou_config = dou_total - gl.get_value("dou_config")
		pitch_2_config = gl.get_value("pitch_2_config")
		roll_2_config = gl.get_value("roll_2_config")


def altitude_calculate_func():
	values = []
	gps_h = gl.get_value("gps_h")
	pitch_2 = gl.get_value("pitch_2")
	roll_2 = gl.get_value("roll_2")
	da_bi_dist = gl.get_value("laser1_dist")
	xiao_bi_dist = gl.get_value("laser2_dist")
	dou_dist = gl.get_value("laser3_dist")

	"""根据gps_h计算斗的高度h_o"""

	# 斗的最低点
	values.append(h_o)
	# values.append(g_h)
	# print("values", values)
	before_is_neg = False
	before_val = values[0]
	for i in range(1, len(values)):
		diff = values[i] - before_val
		if diff >= 0:
			if before_is_neg:
				h_o_min_flag = True
				gl.set_value("h_o_min_flag", h_o_min_flag)  # 挖完一次
				h_o_min = values[i - 1]
				gl.set_value("h_o_min", h_o_min)
				print("h_o_min", h_o_min)

			before_is_neg = False
			before_val = values[i]
			values = []
		else:
			before_is_neg = True
			before_val = values[i]