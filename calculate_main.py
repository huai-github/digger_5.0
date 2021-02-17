from CoordinateTransf import *
from DiggerModelMecharm import *
from DiggerModelWheel import *
import numpy as np
import globalvar as gl
import threading

g_calculate_threadLock = threading.Lock()
values = []


def o_min_altitude(h_o):
    """根据gps_h计算斗的高度h_o"""
    global values
    values.append(h_o)
    before_is_neg = False
    before_val = values[0]
    for i in range(1, len(values)):
        diff = values[i] - before_val
        if diff >= 0:
            if before_is_neg:
                h_o_min_flag = True
                gl.set_value("h_o_min_flag", h_o_min_flag)  # 挖完一次
                h_o_min = values[i - 1]
                gl.set_value("h_o_min", h_o_min)  # 最低点的值---ui显示、4g发送
                # print("h_o_min", h_o_min)
            before_is_neg = False
            before_val = values[i]
            values = []
        else:  # diff >= 0:
            before_is_neg = True
            before_val = values[i]


def thread_calculate_func():
    g_calculate_threadLock.acquire()
    # 顶端天线的GPS坐标
    # gps_x = 482471.061
    # gps_y = 4042628.707
    # gps_h = 68.213
    gps_x = gl.get_value("gps_x")
    gps_y = gl.get_value("gps_y")
    gps_h = gl.get_value("gps_h")
    orgPos = np.dot(np.array([gps_x, gps_y, gps_h]), 1000)

    # 检测的旋转角度
    # rotX = 10.16
    # rotY = 0.6
    # rotZ = 180.118
    rotX = gl.get_value("roll_3")
    rotY = gl.get_value("pitch_3")
    rotZ = gl.get_value("yaw_3")

    # 存储数据,三轴旋转与原点
    DATA = np.array([
        [rotX, rotY, rotZ],
        orgPos
    ])

    # 大臂小臂检测角度？？？？？注意是roll还是pitch
    # da_bi_angle = 19.7
    # xiao_bi_angle = 130.11
    da_bi_angle = gl.get_value("roll_2_da_bi")  # pitch_2_da_bi
    xiao_bi_angle = gl.get_value("roll_2_xiao_bi")  # pitch_2_XIAO_bi
    armAngle = np.array([da_bi_angle, xiao_bi_angle])

    # 三个激光长度
    # da_bi_laser_len = 1474 - 691
    # xiao_bi_laser_len = 1279 - 965.5
    # dou_laser_len = 792
    da_bi_laser_len = 1474 - gl.get_value("da_bi_laser_len")
    xiao_bi_laser_len = 1279 - gl.get_value("xiao_bi_laser_len")
    dou_laser_len = gl.get_value("dou_laser_len")
    laserLen = np.array([da_bi_laser_len, xiao_bi_laser_len, dou_laser_len])

    # G点测量坐标？？？？？
    detGpsPos_G = np.dot(np.array([482472.627, 4042632.528, 67.441]), 1000)
    # J点测量坐标？？？？？
    detGpsPos_J = np.dot(np.array([482475.593, 4042628.693, 67.357]), 1000)
    # O点测量坐标？？？？？
    detGpsPos_O = np.dot(np.array([482471.156, 4042632.622, 67.692]), 1000)

    # 存储数据，测量G点GPS坐标
    DATA = np.vstack([
        DATA,
        detGpsPos_J
    ])

    # 计算A点GPS坐标
    posAQ = DiggerModelWheel()
    rotAngle = np.array([rotX, rotY, -(180+rotZ)])
    gpsPos_A = CoordinateTransf(orgPos, rotAngle, posAQ[0, :])
    gpsPos_Q = CoordinateTransf(orgPos, rotAngle, posAQ[1, :])

    # 存储数据，倾斜坐标系下AQ坐标
    DATA = np.vstack([DATA, posAQ])
    # 存储数据,旋转后AQ
    DATA = np.vstack([DATA, gpsPos_A - orgPos, gpsPos_Q - orgPos])
    # 存储数据，旋转平移后AQ
    DATA = np.vstack([DATA, gpsPos_A, gpsPos_Q])

    # 计算g,j,o点GPS坐标
    posGJO = DiggerModelMecharm(laserLen, armAngle)

    rotAngle = np.hstack([0, rotY, - (180 + rotZ)])

    # 存储数据,倾斜坐标系下GJO坐标
    DATA = np.vstack([DATA, posGJO])

    gpsPos_GJO = np.zeros(shape=(1, 3))
    for i in range(3):
        posTmp = posGJO[i, :]
        rst = CoordinateTransf(gpsPos_A, rotAngle, posTmp)  # 不绕X轴旋转
        gpsPos_GJO = np.vstack([gpsPos_GJO, rst])

    gpsPos_GJO = np.delete(gpsPos_GJO, 0, 0)  # 删除第一行的全0行

    # 存储数据，旋转后GJO坐标
    DATA = np.vstack([
        DATA,
        gpsPos_GJO[0, :] - gpsPos_A,
        gpsPos_GJO[1, :] - gpsPos_A,
        gpsPos_GJO[2, :] - gpsPos_A
    ])

    # 存储数据，旋转平移后GJO坐标
    DATA = np.vstack([DATA, gpsPos_GJO])

    rst_gps_pos_gjo = gpsPos_GJO[2, :] - (detGpsPos_O + np.array([0, 0, - (2325 - 1343)]))

    # gl.set_value("o_h", rst_gps_pos_gjo[-1])

    # 计算o点的最低点
    o_min_altitude(rst_gps_pos_gjo[-1])

    g_calculate_threadLock.release()
    # return rst_gps_pos_gjo


# if __name__ == '__main__':
#     print(thread_calculate_func())
