# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'digger_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Digger(object):
    def setupUi(self, Digger):
        Digger.setObjectName("Digger")
        Digger.resize(1280, 872)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(Digger)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.groupBox = QtWidgets.QGroupBox(Digger)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.leftLabel = QtWidgets.QLabel(self.groupBox)
        self.leftLabel.setText("")
        self.leftLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.leftLabel.setObjectName("leftLabel")
        self.horizontalLayout.addWidget(self.leftLabel)
        self.line = QtWidgets.QFrame(self.groupBox)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.rightLabel = QtWidgets.QLabel(self.groupBox)
        self.rightLabel.setText("")
        self.rightLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.rightLabel.setObjectName("rightLabel")
        self.horizontalLayout.addWidget(self.rightLabel)
        self.horizontalLayout_6.addLayout(self.horizontalLayout)
        self.verticalLayout_4.addWidget(self.groupBox)
        self.line_2 = QtWidgets.QFrame(Digger)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.verticalLayout_4.addWidget(self.line_2)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.groupBox_2 = QtWidgets.QGroupBox(Digger)
        self.groupBox_2.setTitle("")
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.diggerID_label = QtWidgets.QLabel(self.groupBox_2)
        self.diggerID_label.setStyleSheet("font: 75 9pt \"微软雅黑\";\n"
"font: 14pt \"微软雅黑\";")
        self.diggerID_label.setObjectName("diggerID_label")
        self.horizontalLayout_4.addWidget(self.diggerID_label)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.diggerID = QtWidgets.QLabel(self.groupBox_2)
        self.diggerID.setStyleSheet("font: 12pt \"Consolas\";")
        self.diggerID.setText("")
        self.diggerID.setObjectName("diggerID")
        self.horizontalLayout_4.addWidget(self.diggerID)
        self.horizontalLayout_4.setStretch(0, 10)
        self.horizontalLayout_4.setStretch(1, 1)
        self.horizontalLayout_4.setStretch(2, 30)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.nowcoordinate = QtWidgets.QLabel(self.groupBox_2)
        self.nowcoordinate.setStyleSheet("font: 75 9pt \"微软雅黑\";\n"
"font: 14pt \"微软雅黑\";")
        self.nowcoordinate.setObjectName("nowcoordinate")
        self.horizontalLayout_5.addWidget(self.nowcoordinate)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem1)
        self.nowXY = QtWidgets.QLabel(self.groupBox_2)
        self.nowXY.setStyleSheet("\n"
"font: 12pt \"Consolas\";")
        self.nowXY.setText("")
        self.nowXY.setObjectName("nowXY")
        self.horizontalLayout_5.addWidget(self.nowXY)
        self.horizontalLayout_5.setStretch(0, 10)
        self.horizontalLayout_5.setStretch(1, 1)
        self.horizontalLayout_5.setStretch(2, 30)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.now_deep_label = QtWidgets.QLabel(self.groupBox_2)
        self.now_deep_label.setStyleSheet("font: 75 9pt \"微软雅黑\";\n"
"font: 14pt \"微软雅黑\";")
        self.now_deep_label.setObjectName("now_deep_label")
        self.horizontalLayout_7.addWidget(self.now_deep_label)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem2)
        self.now_deep = QtWidgets.QLabel(self.groupBox_2)
        self.now_deep.setStyleSheet("font: 12pt \"Consolas\";")
        self.now_deep.setText("")
        self.now_deep.setObjectName("now_deep")
        self.horizontalLayout_7.addWidget(self.now_deep)
        self.horizontalLayout_7.setStretch(0, 10)
        self.horizontalLayout_7.setStretch(1, 1)
        self.horizontalLayout_7.setStretch(2, 30)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_9.addWidget(self.groupBox_2)
        self.line_4 = QtWidgets.QFrame(Digger)
        self.line_4.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        self.horizontalLayout_9.addWidget(self.line_4)
        self.groupBox_3 = QtWidgets.QGroupBox(Digger)
        self.groupBox_3.setTitle("")
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.border_warning = QtWidgets.QLabel(self.groupBox_3)
        self.border_warning.setStyleSheet("font: 75 9pt \"微软雅黑\";\n"
"font: 14pt \"微软雅黑\";")
        self.border_warning.setObjectName("border_warning")
        self.verticalLayout.addWidget(self.border_warning)
        self.gps_warning = QtWidgets.QLabel(self.groupBox_3)
        self.gps_warning.setStyleSheet("font: 75 9pt \"微软雅黑\";\n"
"font: 14pt \"微软雅黑\";")
        self.gps_warning.setObjectName("gps_warning")
        self.verticalLayout.addWidget(self.gps_warning)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.line_3 = QtWidgets.QFrame(self.groupBox_3)
        self.line_3.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.horizontalLayout_2.addWidget(self.line_3)
        self.label = QtWidgets.QLabel(self.groupBox_3)
        self.label.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.label.setStyleSheet("font: 75 12pt \"微软雅黑\";")
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_9.addWidget(self.groupBox_3)
        self.horizontalLayout_9.setStretch(0, 5)
        self.horizontalLayout_9.setStretch(2, 5)
        self.verticalLayout_4.addLayout(self.horizontalLayout_9)
        self.verticalLayout_4.setStretch(0, 5)
        self.verticalLayout_4.setStretch(1, 1)
        self.verticalLayout_4.setStretch(2, 2)

        self.retranslateUi(Digger)
        QtCore.QMetaObject.connectSlotsByName(Digger)

    def retranslateUi(self, Digger):
        _translate = QtCore.QCoreApplication.translate
        Digger.setWindowTitle(_translate("Digger", "挖掘机·"))
        self.diggerID_label.setText(_translate("Digger", "挖掘机ID："))
        self.nowcoordinate.setText(_translate("Digger", "当前坐标:"))
        self.now_deep_label.setText(_translate("Digger", "当前深度："))
        self.border_warning.setText(_translate("Digger", "边界提示"))
        self.gps_warning.setText(_translate("Digger", "GPS信号"))
        self.label.setText(_translate("Digger", "说明：红灯表示超出。。。。。"))
