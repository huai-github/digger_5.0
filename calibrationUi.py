# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'calibrationUi.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_calibrationUi(object):
    def setupUi(self, calibrationUi):
        calibrationUi.setObjectName("calibrationUi")
        calibrationUi.resize(1147, 697)
        self.rtnMainUiBtn = QtWidgets.QPushButton(calibrationUi)
        self.rtnMainUiBtn.setGeometry(QtCore.QRect(500, 290, 93, 28))
        self.rtnMainUiBtn.setObjectName("rtnMainUiBtn")

        self.retranslateUi(calibrationUi)
        QtCore.QMetaObject.connectSlotsByName(calibrationUi)

    def retranslateUi(self, calibrationUi):
        _translate = QtCore.QCoreApplication.translate
        calibrationUi.setWindowTitle(_translate("calibrationUi", "calibrationUi"))
        self.rtnMainUiBtn.setText(_translate("calibrationUi", "主界面"))

