# ***************************************************************
# Copyright © wkangk <wangkangchn@163.com>
# 文件名	: logger.py
# 作者	  	: wkangk <wangkangchn@163.com>
# 版本	   	: v1.0
# 描述	   	: 配置日志文件
# 时间	   	: 2021-01-19 11:31
# ***************************************************************
import logging
import os


def setup_logger(filepath):
    """ 日志文件 """
    # 当前时间 模块的文件名
    file_formatter = logging.Formatter(
        # "[%(asctime)s %(filename)s %(funcName)s %(lineno)s] %(levelname)-6s %(message)s",
        "[%(filename)s %(funcName)s %(lineno)s] %(levelname)-6s %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    logger = logging.getLogger('example')
    handler = logging.StreamHandler()   # 输出到显示器
    handler.setFormatter(file_formatter)
    logger.addHandler(handler)

    file_handle_name = "file"
    if file_handle_name in [h.name for h in logger.handlers]:
        return
    if os.path.dirname(filepath) is not '':
        if not os.path.isdir(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))
    # 日志文件
    file_handle = logging.FileHandler(filename=filepath, mode="a")
    file_handle.set_name(file_handle_name)
    file_handle.setFormatter(file_formatter)
    logger.addHandler(file_handle)
    
    logger.setLevel(logging.FATAL)
    # logger.setLevel(logging.ERROR)
    # logger.setLevel(logging.INFO)  
    logger.setLevel(logging.DEBUG)  # 文件中只显示 debug 以上等级的信息

    return logger

# log.debug(light_blue("传感器进程等 pSor_gps_main_lock ..."))


