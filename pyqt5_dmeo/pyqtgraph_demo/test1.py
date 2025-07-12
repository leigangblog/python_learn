#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:test1.py
@time:2023/05/15
@邮箱：leigang431@163.com
"""
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget
import numpy as np


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Multiple Dynamic Plots')
        self.grid_layout = QGridLayout()
        self.central_widget = QWidget(self)
        self.central_widget.setLayout(self.grid_layout)
        self.setCentralWidget(self.central_widget)

        # create 3 PlotWidget objects
        self.plot1 = pg.PlotWidget()
        self.plot2 = pg.PlotWidget()
        self.plot3 = pg.PlotWidget()

        # add to grid layout
        self.grid_layout.addWidget(self.plot1, 0, 0)
        self.grid_layout.addWidget(self.plot2, 0, 1)
        self.grid_layout.addWidget(self.plot3, 1, 0, 1, 2)

        # set up data for each plot
        self.x = np.linspace(0, 10 * np.pi, 1000)
        self.y1 = np.sin(self.x)
        self.y2 = np.cos(self.x)
        self.y3 = np.sin(self.x) + np.cos(self.x)

        # create 3 plot curves
        self.curve1 = self.plot1.plot()
        self.curve2 = self.plot2.plot()
        self.curve3 = self.plot3.plot()

        # start updating plots
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10)

    def update(self):
        # update curves with new data
        self.curve1.setData(self.x, self.y1)
        self.curve2.setData(self.x, self.y2)
        self.curve3.setData(self.x, self.y3)


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()