#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:test2.py
@time:2023/05/15
@邮箱：leigang431@163.com
"""
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow

app = QApplication([])
win = QMainWindow()
win.resize(800, 600)

# create a plot widget in the main window
plot_widget = pg.PlotWidget()
win.setCentralWidget(plot_widget)

# plot some data
x = [1, 2, 3, 4, 5]
y = [2, 4, 6, 8, 10]
plot_widget.plot(x, y)

win.show()
app.exec_()