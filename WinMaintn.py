#!/usr/bin/python3
# coding = utf-8

import datetime
import time

import cv2 as cv
import numpy as np

import globalvar as gl
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


def point_dist(x1, y1, x2, y2):
	""" 两点间的距离 """
	return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def ExtendHitWid(cPt, sPt, ePt):
	"""
	计算高度宽度
	cPt：当前点xy
	sPt:中线起点的xyh或者xyw
	ePt:中线终点的xyh或者xyw
	"""
	# 当前点到当前直线段起点和终点的距离
	cPt2sPtDist = point_dist(cPt[0], cPt[1], sPt[0], sPt[1])
	cPt2ePtDist = point_dist(cPt[0], cPt[1], ePt[0], ePt[1])
	sPt2ePtDist = point_dist(sPt[0], sPt[1], ePt[0], ePt[1])
	# 中线起点终点的直线、当前点与起点的直线、当前点与终点的直线形成的三角形的夹角
	cosAlpha = (cPt2ePtDist ** 2 + sPt2ePtDist ** 2 - cPt2sPtDist ** 2) / (2 * cPt2ePtDist * sPt2ePtDist)
	# 当前点在x轴（中线）的投影
	cPtPrjDist = cPt2ePtDist * cosAlpha
	# 起点与终点斜坡的直线斜率
	k = (sPt[2] - ePt[2]) / (sPt2ePtDist - 0)
	# 当前点的施工高度
	extendRst = (k * cPtPrjDist) + ePt[2]

	return extendRst


def CalDist(x0, y0, x1, y1, x2, y2):
	"""计算点到直线的距离"""
	#  x0,y0 点
	A = y1 - y2
	B = -(x1 - x2)
	C = y1 * (x1 - x2) - x1 * (y1 - y2)
	return abs((A * x0 + B * y0 + C) / (A * A + B * B) ** 0.5)


def SegFun(x1, y1, x2, y2, cx, cy):
	"""判断点与直线的位置关系"""
	return (y1 - y2) * (cx - x1) - (x1 - x2) * (cy - y1)


def GetCurrentSegID(lx, ly, rx, ry, cx, cy, centX, centY):
	"""获取当前点所处的段数"""
	# lx, ly, rx, ry 边界列表
	# cX cY 当前坐标
	# centX 中线x坐标
	segID = -20
	for i in range(len(lx) - 1):
		symI = SegFun(lx[i], ly[i], rx[i], ry[i], cx, cy)
		symI_1 = SegFun(lx[i + 1], ly[i + 1], rx[i + 1], ry[i + 1], cx, cy)
		if symI * symI_1 <= 0:
			segID = i
			break
		else:
			pass

	if segID < -1:
		# 当前点和中线起点的距离
		cPt2CetnSptDist = point_dist(cx, cy, centX[0], centY[0])
		# 当前点和中线终点的距离
		cPt2CentEptDist = point_dist(cx, cy, centX[-1], centY[-1])
		# 距离哪条线近
		if cPt2CetnSptDist < cPt2CentEptDist:
			# 在第1段之前,显示到第一段的距离
			segID = 0
		else:
			# 在最后一段之前,显示到最后一段的距离
			segID = -1

	return segID


def WinMaintnFun():
	imgLft = np.zeros((h, w, 3), np.uint8)
	imgRit = np.zeros((h, w, 3), np.uint8)
	barNum = 8
	xBais = 40  # bar平移
	deep = []
	zoomDeep = []
	absDeep = []

	"""等待数据准备"""
	time.sleep(0.001)
	while True:
		my_lock.CalculatorWinLock.acquire()
		calculate_data_valid_flg = gl.get_value("calculate_data_valid_flg")
		my_lock.CalculatorWinLock.release()

		my_lock.Win4gLock.acquire()
		_4g_data_valid_flg = gl.get_value("_4g_data_valid_flg")
		my_lock.Win4gLock.release()

		if calculate_data_valid_flg and _4g_data_valid_flg:
			break
		else:
			print("\r\n维护线程数据-----未准备完成\r\n")
			print("\n!!!!维护线程未准备完成---计算：%s\t4G：%s\n" % (calculate_data_valid_flg, _4g_data_valid_flg))
		time.sleep(0.1)

	while True:
		print("\r\n*************************************** 界面维护线程已启动 ***************************************\r\n")

		# 全局变量初始化
		main_win_data_valid_flg = False

		# 获取任务数据
		my_lock.Win4gLock.acquire()
		sx_list = gl.get_value('g_start_x_list')  # 所有中线x坐标
		sy_list = gl.get_value('g_start_y_list')  # 所有中线y坐标
		s_height = gl.get_value("g_start_h_list")
		s_width = gl.get_value('g_start_w_list')
		ex_list = gl.get_value('g_end_x_list')
		ey_list = gl.get_value('g_end_y_list')
		e_height = gl.get_value("g_end_h_list")
		e_width = gl.get_value('g_end_w_list')
		my_lock.Win4gLock.release()

		# 获取挖斗当前坐标
		my_lock.CalculatorWinLock.acquire()
		current_o_x = gl.get_value('o_x') / 1000
		current_o_y = gl.get_value('o_y') / 1000
		current_o_h = gl.get_value("o_h") / 1000
		my_lock.CalculatorWinLock.release()

		imgLft[::] = 255  # 画布颜色
		imgRit[::] = 255  # 画布颜色
		currentPoint = [current_o_x, current_o_y]

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
		x_list = (sx_list + ex_list) + (save_line_point_sx_l_list + save_line_point_sx_r_list + save_line_point_ex_l_list + save_line_point_ex_r_list) + (save_intersection_xl + save_intersection_xr)
		x_list.append(currentPoint[0])

		y_list = (sy_list + ey_list) + (save_line_point_sy_l_list + save_line_point_sy_r_list + save_line_point_ey_l_list + save_line_point_ey_r_list) + (save_intersection_yl + save_intersection_yr)
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

		sx_list2[:] = [v - x_min for v in sx_list]  # 中线坐标
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

		# 构造平移后边界点
		borderPt_xl = save_intersection_xl.copy()  # 用于保存平移后挖掘边界区域的点
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
		                        currentPoint_move[0], currentPoint_move[1],
								sx_list2, ey_list2
								)
		# print("IDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDIDID:%d\n" % segID)
		# text = [481096.707 + (481098.148 - 481096.707) / 2, 4044974.111 + (4044972.740 - 4044974.111) / 2]
		# segID = 0
		""" 当前点高度计算 """
		cPtStdH = ExtendHitWid(currentPoint,
							   [sx_list[segID], sy_list[segID], s_height[segID]],
							   [ex_list[segID], ey_list[segID], e_height[segID]]
							   )
		# print("//////////////////////////////////////////////////////////cPtStdH:%f" % cPtStdH)

		""" 当前点宽度计算 """
		cPtStdW = ExtendHitWid(currentPoint,
							   [sx_list[segID], sy_list[segID], s_width[segID]],
							   [ex_list[segID], ey_list[segID], e_width[segID]]
							   )

		# print("//*/*/*/*/*/*/*/*/*/**/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*cPtStdW:%f" % cPtStdW)

		""" 计算到中线距离 """
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
		_, contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)  # 笔记本
		# contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)    # 工控机

		currentPoint_zoom = (
			int(currentPoint_zoom[0]),
			int(currentPoint_zoom[1])
		)

		cv.circle(imgLft, currentPoint_zoom, 4, [255, 0, 0], -1)

		dist = cv.pointPolygonTest(contours[1], currentPoint_zoom, False)
		# print("dist:", dist)

		imgLft = imgLft[::-1, :, :].copy()

		# 打印到线距离
		# print("*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*--*--*-*-*-*-*-cPtStdW:%s\ttestDist:%s\n" % (cPtStdW, testDist))
		text = str(round(cPtStdW - testDist, 3))
		if dist == -1:
			cv.putText(imgLft, text, (10, 30), cv.FONT_HERSHEY_PLAIN, 2.5, (0, 0, 255), 2)
		else:
			cv.putText(imgLft, text, (10, 30), cv.FONT_HERSHEY_PLAIN, 2.5, (0, 255, 0), 2)

		# 维护右边图像
		showDeep = current_o_h - cPtStdH
		deep.append(showDeep)
		if len(deep) > barNum:
			deep.pop(0)

		absDeep[:] = [abs(v) for v in deep]
		maxAbs = max(absDeep)
		zoomFct = 0.4 * h / maxAbs
		zoomDeep[:] = [int(v * zoomFct + h / 2) for v in deep]

		# 画柱状图
		for i in range(len(deep)):
			if zoomDeep[i] < h / 2:
				cv.line(imgRit, (int(i * (w / barNum)) + xBais, int(h / 2)),
				        (int(i * (w / barNum) + xBais), int(zoomDeep[i])),
				        (0, 0, 255), 10)
			else:
				cv.line(imgRit, (int(i * (w / barNum)) + xBais, int(h / 2)),
				        (int(i * (w / barNum) + xBais), int(zoomDeep[i])),
				        (0, 255, 0), 10)

		# 画零线
		cv.line(imgRit, (0, int(h / 2)), (w, int(h / 2)), (0, 0, 0), 10)

		imgRit = imgRit[::-1, :, :].copy()  # 图像上下翻转

		# 显示柱体高度
		for i in range(len(deep)):
			text = str(round(deep[i], 2))
			cv.putText(imgRit, text, (int(i * (w / barNum)) + xBais, h - int(zoomDeep[i]) + 5), cv.FONT_HERSHEY_PLAIN,
			           1.5,
			           (0, 0, 0),
			           1)
		# 显示文字
		text = str(round(showDeep, 2))
		if zoomDeep[-1] < h / 2:
			cv.putText(imgRit, text, (10, 30), cv.FONT_HERSHEY_PLAIN, 2.5, (0, 0, 255), 2)
		else:
			cv.putText(imgRit, text, (10, 30), cv.FONT_HERSHEY_PLAIN, 2.5, (0, 255, 0), 2)

		saveImgRit = imgRit.copy()
		saveImgLft = imgLft.copy()
		main_win_data_valid_flg = True

		with open("lock_log.txt", "a") as file:
			file.write("维护线程--win——ui--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.WinUiLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("维护线程--win——ui--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		# 保存绘制后的左窗口图
		gl.set_value("lftWinImg", saveImgLft)
		gl.set_value("lftWinImgFlg", True)
		# 保存绘制后的右窗口图
		gl.set_value("RitWinImg", saveImgRit)
		gl.set_value("RitWinImgFlg", True)

		gl.set_value("dist", dist)
		gl.set_value("deep", showDeep)

		gl.set_value("main_win_data_valid_flg", main_win_data_valid_flg)
		my_lock.WinUiLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("维护线程--win_ui--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		with open("lock_log.txt", "a") as file:
			file.write("维护线程--win_4g--in" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		my_lock.Win4gLock.acquire()
		with open("lock_log.txt", "a") as file:
			file.write("维护线程--win_4g--ing" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")
		gl.set_value("o_w_4g", cPtStdW)
		gl.set_value("o_w_flg", True)
		my_lock.Win4gLock.release()
		with open("lock_log.txt", "a") as file:
			file.write("维护线程--win_4g--out" + "\t" + datetime.datetime.now().strftime('%H:%M:%S') + "\n")

		time.sleep(0.01)

		print("！！！！！维护线程！！！！！%s\n" % datetime.datetime.now().strftime('%H:%M:%S.%f'))