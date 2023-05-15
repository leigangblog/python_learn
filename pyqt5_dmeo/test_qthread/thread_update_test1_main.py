#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:thread_update_test1_main.py
@time:2023/05/15
@邮箱：leigang431@163.com
"""
import thread_update
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import *
import sys, os
import time


class MyThreadUpdate(thread_update.Ui_mainWindow):
    def __init__(self):
        super(MyThreadUpdate, self).__init__()

    def retranslateUi(self, MainWindow):
        super(MyThreadUpdate, self).retranslateUi(MainWindow)
        ui.pushButton_2.clicked.connect(self.buttonsec_clicked)

    def buttonsec_clicked(self):
        chr_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        for element in chr_list:
            time.sleep(1)
            print(element)
        print('end')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = MyThreadUpdate()
    ui.setupUi(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())