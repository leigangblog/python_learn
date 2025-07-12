import sys
import os
import configparser
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QAbstractTableModel, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QComboBox, QSplitter, QTextEdit, QHeaderView, QMessageBox,
    QTableView, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, QGroupBox,
    QScrollArea, QGridLayout
)


# ================== 可拖动的预期最大值线 ==================
class DraggableMaxLine(pg.InfiniteLine):
    sigPositionChanged = pg.QtCore.Signal(float)

    def __init__(self, pos, angle=0, **kwargs):
        super().__init__(pos=pos, angle=angle, **kwargs)
        self.setCursor(Qt.SizeVerCursor)
        self.dragging = False
        self.setZValue(10)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = self.pos().y() - event.pos().y()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            new_y = event.pos().y() + self.offset
            view_range = self.getViewBox().viewRange()[1]
            new_y = max(view_range[0], min(view_range[1], new_y))
            self.setPos(new_y)
            self.sigPositionChanged.emit(new_y)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()


# ================== 数据表格模型 ==================
class PandasModel(QAbstractTableModel):
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


# ================== CSV 数据模型 ==================
class CSVModel:
    def __init__(self):
        self.df = pd.DataFrame()  # 统一使用df属性[1,6](@ref)
        self.stats = {}
        self.config = self.load_config()
        self.expected_max_lines = {}
        self.selected_columns = []

    def load_config(self):
        config = configparser.ConfigParser()
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
        if column_name in self.expected_max_lines:
            self.expected_max_lines[column_name].hide()

        enabled = self.config.getboolean('EXPECTED_MAX', 'enabled')
        if not enabled:
            return None

        try:
            if column_name in self.config['COLUMN_SPECIFIC']:
                max_value = float(self.config['COLUMN_SPECIFIC'][column_name])
            else:
                max_value = float(self.config.get('EXPECTED_MAX', 'default_value'))
        except (ValueError, KeyError):
            return None

        color = self.config.get('EXPECTED_MAX', 'color')
        width = self.config.getint('EXPECTED_MAX', 'width')
        style = self.config.get('EXPECTED_MAX', 'style')

        pen = pg.mkPen(color=color, width=width)
        if style == 'dash':
            pen.setStyle(Qt.DashLine)
        elif style == 'dot':
            pen.setStyle(Qt.DotLine)
        elif style == 'dash-dot':
            pen.setStyle(Qt.DashDotLine)

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
        if 'COLUMN_SPECIFIC' not in self.config:
            self.config['COLUMN_SPECIFIC'] = {}
        self.config['COLUMN_SPECIFIC'][column_name] = str(new_value)

        try:
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"更新配置文件失败: {e}")

    # ================ 增强的CSV加载方法 ================
    def load_csv(self, file_path):
        try:
            # 尝试UTF-8编码[7](@ref)
            self.df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            # 尝试GBK编码[7](@ref)
            try:
                self.df = pd.read_csv(file_path, encoding='gbk')
            except Exception as e:
                QMessageBox.critical(None, "文件读取错误",
                                     f"无法读取文件: {e}\n请检查文件格式和编码")
                return False
        except Exception as e:
            QMessageBox.critical(None, "文件读取错误",
                                 f"读取CSV失败: {e}")
            return False

        # 清洗列名（移除空格和特殊字符）[7](@ref)
        self.df.columns = [col.strip().replace(' ', '_') for col in self.df.columns]
        self.calculate_stats()
        return True

    def calculate_stats(self):
        self.stats = {}
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                col_stats = {
                    'min': self.df[col].min(),
                    'max': self.df[col].max(),
                    'mean': self.df[col].mean(),  # 修正属性引用[1](@ref)
                    'min_rows': self.df[self.df[col] == self.df[col].min()],
                    'max_rows': self.df[self.df[col] == self.df[col].max()]
                }
                self.stats[col] = col_stats

    def get_plot_data(self, column):
        return self.df[column].values if column in self.df.columns else []

    def set_selected_columns(self, columns):
        self.selected_columns = columns


# ================== 视图模型 ==================
class CSVViewModel:
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

    def get_plot_data(self, column=None):
        col = column or self.current_column
        if col:
            return self.model.get_plot_data(col)
        return []

    def get_expected_max_line(self, column_name):
        line = self.model.create_expected_max_line(column_name)
        if line:
            line.sigPositionChanged.connect(
                lambda pos: self.handle_line_moved(column_name, pos)
            )
            self.current_max_line = line
        return line

    def handle_line_moved(self, column_name, new_y):
        new_value = round(new_y, 2)
        self.model.update_expected_max(column_name, new_value)
        if self.current_max_line:
            self.current_max_line.label.setText(f"预期最大值: {new_value:.2f}")

    def set_selected_columns(self, columns):
        self.model.set_selected_columns(columns)

    def get_multi_plot_data(self):
        return {col: self.model.get_plot_data(col) for col in self.model.selected_columns}


# ================== 多列选择对话框 ==================
class MultiColumnDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择要分析的列")
        self.setMinimumSize(400, 500)

        layout = QVBoxLayout(self)
        label = QLabel("选择要分析的列（可多选）:")
        layout.addWidget(label)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        for col in columns:
            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def selected_columns(self):
        return [self.list_widget.item(i).text()
                for i in range(self.list_widget.count())
                if self.list_widget.item(i).checkState() == Qt.Checked]


# ================== 主界面 ==================
class CSVView(QMainWindow):
    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model
        self.plot_widgets = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('CSV数据分析工具')
        self.setGeometry(100, 100, 1400, 900)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 顶部控制栏
        control_layout = QHBoxLayout()
        self.open_btn = QPushButton('打开CSV文件')
        self.open_btn.clicked.connect(self.open_file)
        self.column_selector = QComboBox()
        self.column_selector.currentIndexChanged.connect(self.update_single_display)
        self.config_btn = QPushButton('配置设置')
        self.config_btn.clicked.connect(self.edit_config)
        self.multi_select_btn = QPushButton('多列选择')
        self.multi_select_btn.clicked.connect(self.select_multiple_columns)
        self.multi_select_btn.setEnabled(False)

        control_layout.addWidget(self.open_btn)
        control_layout.addWidget(QLabel('单列选择:'))
        control_layout.addWidget(self.column_selector)
        control_layout.addWidget(self.config_btn)
        control_layout.addWidget(QLabel('多列分析:'))
        control_layout.addWidget(self.multi_select_btn)
        control_layout.addStretch()

        # 主内容区 - 堆叠布局
        self.stacked_widget = QWidget()
        self.stacked_layout = QVBoxLayout(self.stacked_widget)

        # 单列显示区域
        self.single_display_widget = QWidget()
        single_layout = QVBoxLayout(self.single_display_widget)

        splitter = QSplitter(Qt.Horizontal)
        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.single_plot_widget = pg.PlotWidget()
        self.single_plot_widget.setBackground('w')
        self.single_plot_widget.showGrid(x=True, y=True)
        self.single_plot_widget.addLegend()

        right_layout.addWidget(QLabel('统计信息:'))
        right_layout.addWidget(self.stats_display)
        right_layout.addWidget(QLabel('数据可视化:'))
        right_layout.addWidget(self.single_plot_widget)

        splitter.addWidget(self.table_view)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        single_layout.addWidget(splitter)

        # 多列显示区域
        self.multi_display_widget = QWidget()
        multi_layout = QVBoxLayout(self.multi_display_widget)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.multi_chart_container = QWidget()
        self.chart_grid = QGridLayout(self.multi_chart_container)
        scroll_area.setWidget(self.multi_chart_container)

        multi_layout.addWidget(QLabel('多列数据分析:'))
        multi_layout.addWidget(scroll_area)

        self.stacked_layout.addWidget(self.single_display_widget)
        self.stacked_layout.addWidget(self.multi_display_widget)
        self.multi_display_widget.hide()

        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.stacked_widget)

    # ================ 文件操作 ================
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开CSV文件", "", "CSV文件 (*.csv);;所有文件 (*)"
        )
        if file_path:
            success, columns = self.view_model.load_file(file_path)
            if success:
                self.update_table()
                self.column_selector.clear()
                self.column_selector.addItems(columns)
                if columns:
                    self.column_selector.setCurrentIndex(0)
                    self.multi_select_btn.setEnabled(True)
                self.single_display_widget.show()
                self.multi_display_widget.hide()

    def update_table(self):
        model = PandasModel(self.view_model.model.df)
        self.table_view.setModel(model)

    # ================ 配置操作 ================
    def edit_config(self):
        try:
            if sys.platform == 'win32':
                os.startfile('config.ini')
            elif sys.platform == 'darwin':
                os.system('open config.ini')
            else:
                os.system('xdg-open config.ini')
        except Exception as e:
            QMessageBox.warning(self, "打开失败",
                                f"无法打开配置文件: {e}\n请手动编辑config.ini")

        QMessageBox.information(
            self,
            "配置更新",
            "配置文件已打开。修改后请重新选择列以应用新配置。"
        )

    # ================ 多列选择 ================
    def select_multiple_columns(self):
        dialog = MultiColumnDialog(self.view_model.model.df.columns.tolist(), self)
        if dialog.exec_() == QDialog.Accepted:
            selected = dialog.selected_columns()
            if selected:
                self.view_model.set_selected_columns(selected)
                self.generate_multi_charts(selected)
                self.single_display_widget.hide()
                self.multi_display_widget.show()
            else:
                QMessageBox.warning(self, "选择错误", "请至少选择一列进行分析")

    # ================ 图表生成 ================
    def generate_multi_charts(self, columns):
        # 清除旧图表
        for i in reversed(range(self.chart_grid.count())):
            widget = self.chart_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.plot_widgets.clear()

        # 生成新图表
        row, col = 0, 0
        max_cols = 2

        for column in columns:
            group_box = QGroupBox(column)
            group_layout = QVBoxLayout(group_box)

            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('w')
            plot_widget.showGrid(x=True, y=True)
            plot_widget.setMinimumHeight(300)

            plot_data = self.view_model.get_plot_data(column)
            if plot_data.size > 0:
                plot_widget.plot(plot_data, pen='b', name='实际数据')

                expected_max_line = self.view_model.get_expected_max_line(column)
                if expected_max_line:
                    plot_widget.addItem(expected_max_line)

                plot_widget.setLabel('left', column)
                plot_widget.setLabel('bottom', '行号')

            group_layout.addWidget(plot_widget)
            self.chart_grid.addWidget(group_box, row, col)
            self.plot_widgets[column] = plot_widget

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    # ================ 单列显示更新 ================
    def update_single_display(self):
        column = self.column_selector.currentText()
        stats = self.view_model.get_column_stats(column)

        if stats:
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
            self.single_plot_widget.clear()
            plot_data = self.view_model.get_plot_data()

            if plot_data.size > 0:
                self.single_plot_widget.plot(
                    plot_data,
                    pen='b',
                    name='实际数据',
                    symbol='o',
                    symbolSize=5,
                    symbolBrush='b'
                )

                expected_max_line = self.view_model.get_expected_max_line(column)
                if expected_max_line:
                    self.single_plot_widget.addItem(expected_max_line)

                self.single_plot_widget.setTitle(f"{column} 数据分析")
                self.single_plot_widget.setLabel('left', column)
                self.single_plot_widget.setLabel('bottom', '行号')


# ================== 主程序入口 ==================
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