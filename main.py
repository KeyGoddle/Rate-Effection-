from project import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QApplication

import sys

class MyMainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())