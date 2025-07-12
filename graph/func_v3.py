#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
@author:lei
@file:func_v3.py
@time:2025/07/13
@邮箱：leigang431@163.com
"""
import sys
import os
import configparser
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QAbstractTableModel, QFileSystemWatcher, QTimer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableView, QPushButton, QFileDialog, QLabel, QComboBox,
                             QSplitter, QTextEdit, QHeaderView, QMessageBox)


class DraggableMaxLine(pg.InfiniteLine):
    """可拖动的预期最大值线（核心交互组件）"""
    sigPositionChanged = pg.QtCore.Signal(float)  # 自定义位置变化信号

    def __init__(self, pos, angle=0, **kwargs):
        super().__init__(pos=pos, angle=angle, **kwargs)
        self.setCursor(Qt.SizeVerCursor)  # 设置垂直拖拽光标
        self.dragging = False
        self.setZValue(10)  # 确保线在最上层

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = self.pos().y() - event.pos().y()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            # 将鼠标位置转换为视图坐标
            new_y = event.pos().y() + self.offset
            view_range = self.getViewBox().viewRange()[1]  # 获取Y轴范围
            # 限制在图表范围内
            new_y = max(view_range[0], min(view_range[1], new_y))
            self.setPos(new_y)
            self.sigPositionChanged.emit(new_y)  # 发射位置变化信号
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()


class PandasModel(QAbstractTableModel):
    """数据模型：封装Pandas DataFrame供TableView使用"""

    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            elif orientation == Qt.Vertical:
                return str(self._data.index[section])
        return None


class CSVModel:
    """Model层：支持每列独立配置预期最大值"""

    def __init__(self):
        self.df = pd.DataFrame()
        self.stats = {}
        self.config = self.load_config()
        self.expected_max_lines = {}  # 存储各列的预期最大值线
        self.config_watcher = self.setup_config_watcher()

    def setup_config_watcher(self):
        """设置配置文件监视器"""
        watcher = QFileSystemWatcher()
        if os.path.exists('config.ini'):
            watcher.addPath('config.ini')
        watcher.fileChanged.connect(self.reload_config)
        return watcher

    def reload_config(self, path):
        """热重载配置文件"""
        if path == 'config.ini':
            self.config.read('config.ini')
            QTimer.singleShot(100, self.notify_config_update)  # 延迟避免读写冲突

    def notify_config_update(self):
        """通知视图更新"""
        # 实际项目中应使用信号通知视图层

    def load_config(self):
        """加载配置文件，支持每列独立配置"""
        config = configparser.ConfigParser()
        # 默认配置
        config['EXPECTED_MAX'] = {
            'enabled': 'True',
            'default_value': '100',
            'color': '#00FF00',
            'width': '2',
            'style': 'dash'
        }
        config['COLUMN_SPECIFIC'] = {}

        if os.path.exists('config.ini'):
            config.read('config.ini')
        else:
            with open('config.ini', 'w') as configfile:
                config.write(configfile)

        return config

    def create_expected_max_line(self, column_name):
        """创建指定列的预期最大值线（支持动态更新）"""
        # 清除旧线
        if column_name in self.expected_max_lines:
            self.expected_max_lines[column_name].hide()

        # 检查总开关
        enabled = self.config.getboolean('EXPECTED_MAX', 'enabled')
        if not enabled:
            return None

        try:
            # 优先使用列特定配置
            if column_name in self.config['COLUMN_SPECIFIC']:
                max_value = float(self.config['COLUMN_SPECIFIC'][column_name])
            # 其次使用默认配置
            else:
                max_value = float(self.config.get('EXPECTED_MAX', 'default_value'))
        except (ValueError, KeyError):
            return None

        # 获取样式配置
        color = self.config.get('EXPECTED_MAX', 'color')
        width = self.config.getint('EXPECTED_MAX', 'width')
        style = self.config.get('EXPECTED_MAX', 'style')

        # 创建线条样式
        pen = pg.mkPen(color=color, width=width)
        if style == 'dash':
            pen.setStyle(Qt.DashLine)
        elif style == 'dot':
            pen.setStyle(Qt.DotLine)
        elif style == 'dash-dot':
            pen.setStyle(Qt.DashDotLine)

        # 创建带标签的可拖拽线
        line = DraggableMaxLine(
            pos=max_value,
            angle=0,
            pen=pen,
            label=f'预期最大值: {max_value:.2f}',
            labelOpts={
                'position': 0.95,
                'color': color,
                'fill': (200, 200, 200, 100),
                'movable': True
            }
        )
        self.expected_max_lines[column_name] = line
        return line

    def update_expected_max(self, column_name, new_value):
        """更新指定列的预期最大值配置"""
        # 更新内存配置
        if 'COLUMN_SPECIFIC' not in self.config:
            self.config['COLUMN_SPECIFIC'] = {}
        self.config['COLUMN_SPECIFIC'][column_name] = str(new_value)

        # 更新文件配置
        try:
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"更新配置文件失败: {e}")

    # 其余方法保持原有实现...
    def load_csv(self, file_path):
        try:
            self.df = pd.read_csv(file_path)
            self.calculate_stats()
            return True
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False

    def calculate_stats(self):
        self.stats = {}
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                col_stats = {
                    'min': self.df[col].min(),
                    'max': self.df[col].max(),
                    'mean': self.df[col].mean(),
                    'min_rows': self.df[self.df[col] == self.df[col].min()],
                    'max_rows': self.df[self.df[col] == self.df[col].max()]
                }
                self.stats[col] = col_stats

    def get_plot_data(self, column):
        return self.df[column].values if column in self.df.columns else []


class CSVViewModel:
    """ViewModel层：协调数据访问和交互逻辑"""

    def __init__(self, model):
        self.model = model
        self.current_column = None
        self.current_max_line = None

    def load_file(self, file_path):
        success = self.model.load_csv(file_path)
        return success, self.model.df.columns.tolist() if success else []

    def get_column_stats(self, column):
        if column in self.model.stats:
            self.current_column = column
            return self.model.stats[column]
        return None

    def get_plot_data(self):
        if self.current_column:
            return self.model.get_plot_data(self.current_column)
        return []

    def get_expected_max_line(self, column_name):
        """获取指定列的预期最大值线并连接信号"""
        line = self.model.create_expected_max_line(column_name)
        if line:
            # 连接拖动信号到更新逻辑
            line.sigPositionChanged.connect(
                lambda pos: self.handle_line_moved(column_name, pos)
            )
            self.current_max_line = line
        return line

    def handle_line_moved(self, column_name, new_y):
        """处理线拖动事件（核心交互逻辑）"""
        # 实际应用中应转换坐标系（此处简化演示）
        new_value = round(new_y, 2)
        self.model.update_expected_max(column_name, new_value)

        # 更新标签
        if self.current_max_line:
            self.current_max_line.label.setText(f"预期最大值: {new_value:.2f}")


class CSVView(QMainWindow):
    """View层：用户界面和交互呈现"""

    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('CSV数据分析工具 (动态预期值)')
        self.setGeometry(100, 100, 1200, 800)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 顶部控制栏
        control_layout = QHBoxLayout()
        self.open_btn = QPushButton('打开CSV文件')
        self.open_btn.clicked.connect(self.open_file)
        self.column_selector = QComboBox()
        self.column_selector.currentIndexChanged.connect(self.update_display)
        self.config_btn = QPushButton('配置设置')
        self.config_btn.clicked.connect(self.edit_config)
        control_layout.addWidget(self.open_btn)
        control_layout.addWidget(QLabel('选择列:'))
        control_layout.addWidget(self.column_selector)
        control_layout.addWidget(self.config_btn)
        control_layout.addStretch()

        # 主内容区
        splitter = QSplitter(Qt.Horizontal)

        # 表格视图
        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 统计信息显示
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)

        # 图表区域
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()

        # 右侧面板布局
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel('统计信息:'))
        right_layout.addWidget(self.stats_display)
        right_layout.addWidget(QLabel('数据可视化:'))
        right_layout.addWidget(self.plot_widget)

        splitter.addWidget(self.table_view)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])

        main_layout.addLayout(control_layout)
        main_layout.addWidget(splitter)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开CSV文件", "", "CSV文件 (*.csv)"
        )
        if file_path:
            success, columns = self.view_model.load_file(file_path)
            if success:
                self.update_table()
                self.column_selector.clear()
                self.column_selector.addItems(columns)
                if columns:
                    self.column_selector.setCurrentIndex(0)

    def edit_config(self):
        try:
            os.startfile('config.ini')  # Windows
        except:
            try:
                os.system('open config.ini')  # macOS
            except:
                os.system('xdg-open config.ini')  # Linux

        QMessageBox.information(
            self,
            "配置更新",
            "配置文件已打开。修改后请重新选择列以应用新配置。"
        )

    def update_table(self):
        model = PandasModel(self.view_model.model.df)
        self.table_view.setModel(model)

    def update_display(self):
        column = self.column_selector.currentText()
        stats = self.view_model.get_column_stats(column)

        if stats:
            # 显示统计信息
            stats_text = f"=== {column} ===\n"
            stats_text += f"最小值: {stats['min']:.4f}\n"
            stats_text += f"最大值: {stats['max']:.4f}\n"
            stats_text += f"平均值: {stats['mean']:.4f}\n\n"

            stats_text += "最小值所在行:\n"
            for _, row in stats['min_rows'].iterrows():
                stats_text += f"• 行{row.name + 1}: {row.to_dict()}\n"

            stats_text += "\n最大值所在行:\n"
            for _, row in stats['max_rows'].iterrows():
                stats_text += f"• 行{row.name + 1}: {row.to_dict()}\n"

            self.stats_display.setText(stats_text)

            # 更新图表
            self.plot_widget.clear()
            plot_data = self.view_model.get_plot_data()

            if plot_data.size > 0:
                # 绘制主数据线
                self.plot_widget.plot(
                    plot_data,
                    pen='b',
                    name='实际数据',
                    symbol='o',
                    symbolSize=5,
                    symbolBrush='b'
                )

                # 添加预期最大值线（带拖动功能）
                expected_max_line = self.view_model.get_expected_max_line(column)
                if expected_max_line:
                    self.plot_widget.addItem(expected_max_line)

                self.plot_widget.setTitle(f"{column} 数据分析")
                self.plot_widget.setLabel('left', column)
                self.plot_widget.setLabel('bottom', '行号')


def main():
    app = QApplication(sys.argv)

    # 初始化MVVM组件
    model = CSVModel()
    view_model = CSVViewModel(model)
    view = CSVView(view_model)

    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()