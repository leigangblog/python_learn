import thread_update
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import *
import sys, os
import time


class ButtonOne(QThread):
    _signal = pyqtSignal()
    _signalForText = pyqtSignal(str)

    def __init__(self):
        super(ButtonOne, self).__init__()

    def write(self, text):
        self.signalForText.emit(text)

    def run(self):
        for i in range(15):
            time.sleep(1)
            print(i)
        print('end')
        self._signal.emit()

    @property
    def signalForText(self):
        return self._signalForText

    def flush(self):
        pass

class ButtonSec(QThread):
    def __init__(self):
        super(ButtonSec, self).__init__()

    def run(self):
        chr_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        for element in chr_list:
            time.sleep(1)
            print(element)
        print('end')


class MyThreadUpdate(thread_update.Ui_mainWindow):
    def __init__(self):
        super(MyThreadUpdate, self).__init__()
        self.thread_buttonsec = ButtonSec()
        self.thread_buttonone = ButtonOne()
        self.thread_buttonone.signalForText.connect(self.updateText)
        sys.stdout = self.thread_buttonone

    def retranslateUi(self, MainWindow):
        super(MyThreadUpdate, self).retranslateUi(MainWindow)
        ui.button_1.clicked.connect(self.buttonone_clicked)
        ui.pushButton_2.clicked.connect(self.buttonsec_clicked)

    def updateText(self, text):
        cursor = self.text_1.textCursor()
        cursor.insertText(text)
        self.text_1.setTextCursor(cursor)
        self.text_1.ensureCursorVisible()

    def buttonone_clicked(self):
        self.thread_buttonone.start()

    def buttonone_clicked(self):
        self.button_1.setEnabled(False)
        self.thread_buttonone.start()
        self.thread_buttonone._signal.connect(self.enableButtonOne)

    def enableButtonOne(self):
        self.button_1.setEnabled(True)

    def buttonsec_clicked(self):
        self.thread_buttonsec.start()
        # chr_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        # for element in chr_list:
        #     time.sleep(1)
        #     print(element)
        # print('end')
        # 测试打开文件夹
        filepath=os.path.join(os.getcwd(),'./test_folder')
        os.startfile(filepath)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = MyThreadUpdate()
    ui.setupUi(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())

