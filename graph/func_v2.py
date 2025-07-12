import sys
import pandas as pd
import pyqtgraph as pg
import configparser
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QPushButton, QFileDialog, QLabel, QComboBox,
    QSplitter, QTextEdit, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QAbstractTableModel


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
        self.max_line = None
        self.expected_max_lines = {}  # 存储各列的预期最大值线

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

        # 列特定配置示例（实际使用时通过配置文件添加）
        config['COLUMN_SPECIFIC'] = {
            'Age': '50',
            'Salary': '100000',
            'Temperature': '37.5'
        }

        if os.path.exists('config.ini'):
            config.read('config.ini')
        else:
            with open('config.ini', 'w') as configfile:
                config.write(configfile)

        return config

    def create_expected_max_line(self, column_name):
        """创建指定列的预期最大值线"""
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

        # 创建带标签的横线
        line = pg.InfiniteLine(
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

    def load_csv(self, file_path):
        """加载CSV文件并计算统计信息"""
        try:
            self.df = pd.read_csv(file_path)
            self.calculate_stats()
            return True
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False

    def calculate_stats(self):
        """计算每列的统计信息[2](@ref)"""
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
        """获取绘图数据"""
        return self.df[column].values if column in self.df.columns else []


class CSVViewModel:
    """ViewModel层：协调数据访问"""

    def __init__(self, model):
        self.model = model
        self.current_column = None

    def load_file(self, file_path):
        success = self.model.load_csv(file_path)
        return success, self.model.df.columns.tolist() if success else []

    def get_column_stats(self, column):
        """获取指定列的统计信息"""
        if column in self.model.stats:
            self.current_column = column
            return self.model.stats[column]
        return None

    def get_plot_data(self):
        """获取当前列的绘图数据"""
        if self.current_column:
            return self.model.get_plot_data(self.current_column)
        return []

    def get_expected_max_line(self, column_name):
        """获取指定列的预期最大值线"""
        return self.model.create_expected_max_line(column_name)


class CSVView(QMainWindow):
    """View层：用户界面"""

    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('CSV数据分析工具 (多列预期值)')
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

        # 添加所有组件到主布局
        main_layout.addLayout(control_layout)
        main_layout.addWidget(splitter)

    def open_file(self):
        """打开CSV文件[3](@ref)"""
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
        """编辑配置文件"""
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
        """更新表格视图"""
        model = PandasModel(self.view_model.model.df)
        self.table_view.setModel(model)

    def update_display(self):
        """更新统计信息和图表"""
        column = self.column_selector.currentText()
        stats = self.view_model.get_column_stats(column)

        if stats:
            # 显示统计信息[5](@ref)
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

                # 添加预期最大值线
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