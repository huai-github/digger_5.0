# https://blog.csdn.net/fireflychh/article/details/82352710
# https://blog.csdn.net/deng_sai/article/details/21169997/?utm_medium=distribute.pc_relevant.none-task-blog-baidujs_baidulandingword-6&spm=1001.2101.3001.4242
import numpy as np


def CoordinateTransf(org=None, angle=None, xyz=None):
	# % org：旋转轴的GPS坐标
	# % angle: 计算挖掘机模型的坐标系统相对于大地坐标系统旋转角度
	# % xyz：当前点在模型坐标系内的坐标
	rx = angle[0] * np.pi / 180    # np.np.dot(a, b, out=None)  #该函数的作用是获取两个元素a,b的乘积.
	ry = angle[1] * np.pi / 180
	rz = angle[2] * np.pi / 180

	RZ = np.array([
		[np.cos(rz), - np.sin(rz), 0],
		[np.sin(rz), np.cos(rz), 0],
		[0, 0, 1]
	])

	RY = np.array([
		[np.cos(ry), 0, np.sin(ry)],
		[0, 1, 0],
		[- np.sin(ry), 0, np.cos(ry)]
	])

	RX = np.array([
		[1, 0, 0],
		[0, np.cos(rx), - np.sin(rx)],
		[0, np.sin(rx), np.cos(rx)]
	])

	xyz_m = np.dot(np.dot(np.dot(RZ, RY), RX), xyz.T)  #np.dot(a, b, out=None)  #该函数的作用是获取两个元素a,b的乘积.
	rst = xyz_m.T + org

	return rst
