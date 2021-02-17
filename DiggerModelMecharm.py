# 该程序是挖掘机机械臂模型，以大臂底端为原心，大臂所在平面的水平线为y轴，
# x轴平行与转盘，与y轴垂直
from math import acos
import numpy as np
# from smop.libsmop import *


def DiggerModelMecharm(laserLen=None, angle=None):
	# laserLen: 参数分别是大臂、小臂、挖斗对应的激光长度
	# angle: 大臂、小臂角度传感器的角度

	# 解析输入参数
	dlt_bc = laserLen[0]
	dlt_de = laserLen[1]
	dlt_fi = laserLen[2]

	a_ag_angle = angle[0]  # 角度传感器检测角度
	a_gj_angle = angle[1]

	# 挖掘机结构参数
	l_bc_nls = 691
	l_de_nls = 965.5
	l_fi_nls = 701.125

	# 各点的高程,h表示高程，g表示对应的点
	l_ac = 1460
	l_ab = 402
	l_ag = 3000
	l_ad = 1911
	l_bc = l_bc_nls + dlt_bc
	l_cg = 1776
	l_cd = 591.4765
	l_dg = 1724
	l_de = l_de_nls + dlt_de
	l_eg = 492
	l_eh = 1794
	l_fg = 382.2643
	l_fh = 1232
	l_fi = l_fi_nls + dlt_fi
	l_gh = 1360.1
	l_gj = 1600
	l_hi = 338
	l_hj = 243
	l_ik = 317
	l_ij = 0
	l_jk = 260
	l_jo = 942
	l_ko = 1048

	y_a = 0
	y_g = 0
	y_j = 0
	y_o = 0
	z_a = 0
	z_g = 0
	z_j = 0
	z_o = 0

	a_ag = np.dot(a_ag_angle, np.pi) / 180
	a_gj = np.dot(- (90 - a_gj_angle), np.pi) / 180
	a_ghj = acos((l_gh ** 2 + l_hj ** 2 - l_gj ** 2) / (np.dot(np.dot(2, l_gh), l_hj)))
	a_ghf = acos((l_gh ** 2 + l_fh ** 2 - l_fg ** 2) / (np.dot(np.dot(2, l_gh), l_fh)))
	a_fhi = acos((l_fh ** 2 + l_hi ** 2 - l_fi ** 2) / (np.dot(np.dot(2, l_fh), l_hi)))
	a_jhi = np.dot(2, np.pi) - a_ghj - a_ghf - a_fhi
	l_ij = (l_hi ** 2 + l_hj ** 2 - np.dot(np.dot(np.dot(2, l_hi), l_hj), np.cos(a_jhi))) ** 0.5
	a_hji = acos((l_hj ** 2 + l_ij ** 2 - l_hi ** 2) / (np.dot(np.dot(2, l_hj), l_ij)))
	a_ijk = acos((l_ij ** 2 + l_jk ** 2 - l_ik ** 2) / (np.dot(np.dot(2, l_ij), l_jk)))
	a_hjk = a_hji + a_ijk
	a_jg = np.pi + a_gj
	a_gjh = acos((l_gj ** 2 + l_hj ** 2 - l_gh ** 2) / (np.dot(np.dot(2, l_gj), l_hj)))
	a_kjo = acos((l_jk ** 2 + l_jo ** 2 - l_ko ** 2) / (np.dot(np.dot(2, l_jk), l_jo)))
	a_jo = a_jg - (a_gjh + a_hjk + a_kjo)
	z_g = z_a + np.dot(l_ag, np.sin(a_ag))
	y_g = y_a + np.dot(l_ag, np.cos(a_ag))
	z_g = z_g + np.dot(angle[0], 0.709) + 257.8333
	y_g = y_g - np.dot(6.495, angle[0]) + 3.9874
	z_j = z_g - np.dot(l_gj, np.cos(a_gj))
	y_j = y_g + np.dot(l_gj, np.sin(a_gj))
	z_o = z_j - np.dot(l_jo, np.cos(a_jo))
	y_o = y_j + np.dot(l_jo, np.sin(a_jo))

	# pp = concat([0, 11, 22])
	p_a = np.array([0, y_a, z_a])
	p_g = np.array([0, y_g, z_g])
	p_j = np.array([0, y_j, z_j])
	p_o = np.array([0, y_o, z_o])

	rst = np.vstack([
		p_g, p_j, p_o
	])
	return rst


# if __name__ == '__main__':
# 	print(DiggerModelMecharm())