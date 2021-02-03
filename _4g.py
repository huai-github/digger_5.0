import ast
import json
from time import sleep


class Heart(object):
	def __init__(self, messageTypeId, diggerId):
		self.heart_dict = {
			"messageTypeId": messageTypeId,
			"diggerId": diggerId,  # 挖掘机ID
		}

	def send_heart_msg(self, com):
		"""发送心跳"""
		send_buf_json = json.dumps(self.heart_dict)
		com.send_data(send_buf_json.encode('utf-8'))
		com.send_bytes('\n'.encode('utf-8'))
		print("send_buf_json", send_buf_json)

	def rec_heart_msg(self):
		pass


class SendMessage(object):
	def __init__(self, messageTypeId, diggerId, x, y, h, w):
		self.send_msg_dict = {
			"messageTypeId": messageTypeId,
			"diggerId": diggerId,
			"x": x,  # 单位为米，精确到厘米
			"y": y,
			"h": h,
			"w": w,
		}

	def switch_to_json(self):
		return json.dumps(self.send_msg_dict)


def task_switch_dict(rec_buf):
	rec_buf = rec_buf[0:-1]  # 去掉'\n'
	rec_to_str = str(rec_buf, encoding="utf-8")  # bytes -> str，不是dict！！！
	rec_buf_dict = ast.literal_eval(rec_to_str)  # str -> dict
	return rec_buf_dict


def get_xyhw(rec_buf_dict):
	"""将所有的x存在都x列表中"""
	start_point_x = []
	start_point_y = []
	start_point_h = []
	start_point_w = []
	end_point_x = []
	end_point_y = []
	end_point_h = []
	end_point_w = []
	xy_list = rec_buf_dict["list"]
	for xyhw_dict in xy_list:
		for k, v in xyhw_dict.items():
			if k == "startX":
				start_point_x.append(v)
			if k == "startY":
				start_point_y.append(v)
			if k == "startH":
				start_point_h.append(v)
			if k == "startW":
				start_point_w.append(v)
			if k == "endX":
				end_point_x.append(v)
			if k == "endY":
				end_point_y.append(v)
			if k == "endH":
				end_point_h.append(v)
			if k == "endW":
				end_point_w.append(v)

	return start_point_x, start_point_y, start_point_h, start_point_w, \
	       end_point_x, end_point_y, end_point_h, end_point_w
