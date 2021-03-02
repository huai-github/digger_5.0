#!/usr/bin/python3
# coding = utf-8

import time

import cv2 as cv
import numpy as np

import globalvar as gl
from globalvar import data_ready_flg
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


def SegFun(x1, y1, x2, y2, cx, cy):
	# 判断点与直线的位置关系
	return (y1 - y2) * (cx - x1) - (x1 - x2) * (cy - y1)


def GetCurrentSegID(lx, ly, rx, ry, cx, cy):
	# 获取当前点所处的段数
	# cX cY当前坐标
	segID = -1
	for i in range(len(lx) - 1):
		symI = SegFun(lx[i], ly[i], rx[i], ry[i], cx, cy)
		symI_1 = SegFun(lx[i + 1], ly[i + 1], rx[i + 1], ry[i + 1], cx, cy)
		if symI * symI_1 <= 0:
			segID = i
			break
		else:
			pass
	return segID


def CalDist(x0, y0, x1, y1, x2, y2):
	# 计算点到直线的距离
	A = y1 - y2
	B = -(x1 - x2)
	C = y1 * (x1 - x2) - x1 * (y1 - y2)
	return abs((A * x0 + B * y0 + C) / (A * A + B * B) ** 0.5)


def WinMaintnFun():
	imgLft = np.zeros((h, w, 3), np.uint8)
	imgRit = np.zeros((h, w, 3), np.uint8)
	barNum = 5
	xBais = 40  # bar平移
	deep = []
	zoomDeep = []
	absDeep = []
	"""等待数据准备"""
	time.sleep(0.001)
	while True:
		if data_ready_flg.calculate_data_ready_flg and data_ready_flg._4g_data_ready_flg:
			data_ready_flg.calculate_data_ready_flg = False
			data_ready_flg._4g_data_ready_flg = False
			break
		else:
			print("\r\n维护线程数据-----未准备完成\r\n")
			print("calculate_data_ready_flg:",data_ready_flg.calculate_data_ready_flg)
			print("_4g_data_ready_flg:",data_ready_flg._4g_data_ready_flg)

	while True:
		print("\r\n----------------------------------------界面维护线程已启动----------------------------------------\r\n")
		# 获取任务数据
		sx_list = gl.get_value('g_start_x_list')
		sy_list = gl.get_value('g_start_y_list')
		s_width = gl.get_value('g_start_w_list')
		ex_list = gl.get_value('g_end_x_list')
		ey_list = gl.get_value('g_end_y_list')
		e_width = gl.get_value('g_end_w_list')

		# 获取挖斗当前坐标
		nowX = gl.get_value('o_x') / 1000
		nowY = gl.get_value('o_y') / 1000

		imgLft[::] = 255  # 画布
		imgRit[::] = 255  # 画布
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

		# 用于保存平移后挖掘边界区域的点
		borderPt_xl = []
		borderPt_xr = []
		borderPt_yl = []
		borderPt_yr = []

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

		# 构 造平移后边界点
		borderPt_xl = save_intersection_xl.copy()
		borderPt_xr = save_intersection_xr.copy()
		borderPt_yl = save_intersection_yl.copy()
		borderPt_yr = save_intersection_yr.copy()

		# 将首尾的边界点加入
		borderPt_xl.insert(0, save_line_point_sx_l_list[0])
		borderPt_xl.append(save_line_point_ex_l_list[-1])

		borderPt_yl.insert(0, save_line_point_sy_l_list[0])
		borderPt_yl.append(save_line_point_ey_l_list[-1])

		borderPt_xr.insert(0, save_line_point_sx_r_list[0])
		borderPt_xr.append(save_line_point_sx_r_list[0])

		borderPt_yr.insert(0, save_line_point_sy_r_list[0])
		borderPt_yr.append(save_line_point_ey_r_list[-1])

		# 判断当前点所处的段号
		segID = GetCurrentSegID(borderPt_xl, borderPt_yl,
								borderPt_xr, borderPt_yr,
								currentPoint_move[0], currentPoint_move[1]
								)

		# 计算到中线距离
		testDist = CalDist(currentPoint_move[0], currentPoint_move[1],
						   sx_list2[segID], sy_list2[segID],
						   ex_list2[segID], ey_list2[segID])

		# 找xy的最大差值
		x_delta_max = x_max - x_min
		y_delta_max = y_max - y_min

		# 缩放因子
		# global zoom_x, zoom_y
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

		"""画线"""
		# 中线
		for i in range(len(sx_list2)):
			cv.line(imgLft, (int(sx_list2[i]), int(sy_list2[i])), (int(ex_list2[i]), int(ey_list2[i])), (0, 255, 0), 1)

		# 如果交点存在
		if save_intersection_xl:
			# 下面偏移的线
			# 地点到第一个交点
			cv.line(imgLft,
					(int(save_line_point_sx_l_list[0]), int(save_line_point_sy_l_list[0])),
					(int(save_intersection_xl[0]), int(save_intersection_yl[0])),
					(0, 0, 255),
					2)
			# 交点之间的连线
			for i in range(len(save_intersection_xl) - 1):
				cv.line(imgLft,
						(int(save_intersection_xl[i]), int(save_intersection_yl[i])),
						(int(save_intersection_xl[i + 1]), int(save_intersection_yl[i + 1])),
						(0, 0, 255),
						2)
			# 交点到最后一个端点
			cv.line(imgLft,
					(int(save_intersection_xl[-1]), int(save_intersection_yl[-1])),
					(int(save_line_point_ex_l_list[-1]), int(save_line_point_ey_l_list[-1])),
					(0, 0, 255),
					2)

			# 上面偏移的线
			# 地点到第一个交点
			cv.line(imgLft,
					(int(save_line_point_sx_r_list[0]), int(save_line_point_sy_r_list[0])),
					(int(save_intersection_xr[0]), int(save_intersection_yr[0])),
					(0, 0, 255),
					2)
			# 交点之间的连线
			for i in range(len(save_intersection_xr) - 1):
				cv.line(imgLft,
						(int(save_intersection_xr[i]), int(save_intersection_yr[i])),
						(int(save_intersection_xr[i + 1]), int(save_intersection_yr[i + 1])),
						(0, 0, 255),
						2)
			# 交点到最后一个端点
			cv.line(imgLft,
					(int(save_intersection_xr[-1]), int(save_intersection_yr[-1])),
					(int(save_line_point_ex_r_list[-1]), int(save_line_point_ey_r_list[-1])),
					(0, 0, 255),
					2)

		# 如果交点不存在
		if not save_intersection_xl:
			cv.line(imgLft,
					(int(save_line_point_sx_l_list[0]), int(save_line_point_sy_l_list[0])),
					(int(save_line_point_ex_l_list[-1]), int(save_line_point_ey_l_list[-1])),
					(0, 0, 255),
					2)

			cv.line(imgLft,
					(int(save_line_point_sx_r_list[0]), int(save_line_point_sy_r_list[0])),
					(int(save_line_point_ex_r_list[-1]), int(save_line_point_ey_r_list[-1])),
					(0, 0, 255),
					2)

		# 闭合首
		cv.line(imgLft,
				(int(save_line_point_sx_l_list[0]), int(save_line_point_sy_l_list[0])),
				(int(save_line_point_sx_r_list[0]), int(save_line_point_sy_r_list[0])),
				(0, 0, 255),
				2)

		# 闭合尾
		cv.line(imgLft,
				(int(save_line_point_ex_l_list[-1]), int(save_line_point_ey_l_list[-1])),
				(int(save_line_point_ex_r_list[-1]), int(save_line_point_ey_r_list[-1])),
				(0, 0, 255),
				2)

		gray = cv.cvtColor(imgLft, cv.COLOR_BGR2GRAY)
		ret, binary = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)  # 转为二值图
		# _, contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
		contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

		currentPoint_zoom = (
			int(currentPoint_zoom[0]),
			int(currentPoint_zoom[1])
		)

		cv.circle(imgLft, currentPoint_zoom, 4, [255, 0, 0], -1)

		dist = cv.pointPolygonTest(contours[1], currentPoint_zoom, False)
		# print("dist:", dist)
		gl.set_value("dist", dist)

		imgLft = imgLft[::-1, :, :].copy()

		# 打印到中线距离
		text = str(round(testDist, 3))
		cv.putText(imgLft, text, (currentPoint_zoom[0], h - currentPoint_zoom[1]), cv.FONT_HERSHEY_PLAIN, 2.0, (0, 0, 255),
				   2)

		# 保存绘制后的左窗口图
		saveImg = imgLft.copy()
		gl.set_value("lftWinImg", saveImg)
		gl.set_value("lftWinImgFlg", True)

		# 维护右边图像
		# time_now = datetime.datetime.now().strftime('%H:%M:%S.%f')
		# print("11111111111111111111111111111111111111111111111111111111", time_now)

		deep.append(gl.get_value("o_h") / 1000 - gl.get_value("g_start_h_list")[0])
		if len(deep) > barNum:
			deep.pop(0)

		absDeep[:] = [abs(v) for v in deep]
		maxAbs = max(absDeep)
		zoomFct = 0.4 * h / maxAbs
		zoomDeep[:] = [int(v * zoomFct + h / 2) for v in deep]

		# 画柱状图
		red = (0, 0, 255)
		green = (0, 255, 0)
		for i in range(len(deep)):
			if zoomDeep[i] < h / 2:
				cv.line(imgRit, (int(i * (w / barNum)) + xBais, int(h / 2)), (int(i * (w / barNum) + xBais), int(zoomDeep[i])),
						red, 10)
			else:
				cv.line(imgRit, (int(i * (w / barNum)) + xBais, int(h / 2)), (int(i * (w / barNum) + xBais), int(zoomDeep[i])),
						green, 10)

		# 画零线
		cv.line(imgRit, (0, int(h / 2)), (w, int(h / 2)), (0, 0, 0), 10)

		imgRit = imgRit[::-1, :, :].copy()  # 图像上下翻转

		# 显示柱体高度
		for i in range(len(deep)):
			text = str(round(deep[i], 3))
			cv.putText(imgRit, text, (int(i * (w / barNum)) + xBais, h - int(zoomDeep[i]) + 5),  cv.FONT_HERSHEY_PLAIN, 1.5,
			           (0, 0, 0),
			           1)
			
		# 保存绘制后的右窗口图
		saveImg = imgRit.copy()
		gl.set_value("RitWinImg", saveImg)
		gl.set_value("RitWinImgFlg", True)

		time.sleep(0.1)

		# time_now = datetime.datetime.now().strftime('%H:%M:%S.%f')
		# print("222222222222222222222222222222222222222222222222222222222", time_now)

