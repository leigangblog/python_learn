#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:func1.py
@time:2025/07/13
@邮箱：leigang431@163.com
"""
import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

app = QApplication(sys.argv)
win = pg.PlotWidget(title="动态曲线与标记")
win.setBackground('w')  # 白色背景

# 初始数据
x = np.linspace(0, 10, 100)
y = np.sin(x)
curve = win.plot(x, y, pen='b')

# 动态更新
def update():
    global y
    y = np.roll(y, -1)
    y[-1] = np.sin(np.random.rand() * 10)
    curve.setData(x, y)

timer = QTimer()
timer.timeout.connect(update)
timer.start(100)  # 100ms更新

# 点击添加标记点
def add_marker(event):
    pos = win.plotItem.vb.mapSceneToView(event.scenePos())
    marker = pg.ScatterPlotItem(pos=[(pos.x(), pos.y())], size=10, brush='r')
    win.addItem(marker)

win.scene().sigMouseClicked.connect(add_marker)
win.show()
sys.exit(app.exec_())