from PyQt5.QtWidgets import QWidget
import calibrationUi
from runUI import MyWindows


class CalibrationUi(QWidget, calibrationUi.Ui_calibrationUi):
	def __init__(self):
		super().__init__()
		self.setupUi(self)
		self.rtnMainUiBtn.clicked.connect(self.switchUiFunc)

	def switchUiFunc(self):
		self.hide()
		self.mainUi = MyWindows()
		# self.mainUi.showFullScreen()  # 窗口全屏显示
		# self.mainUi.showMaximized()
		self.mainUi.show()


