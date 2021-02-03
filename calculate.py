


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