import sys

from PyQt5.QtWidgets import QApplication

from textshot.textshot import *

if __name__ == "__main__":
    app = QApplication(sys.argv)  # 在 QApplication 方法中使用，创建应用程序对象
    myWin = PickTextMainWindow()  # 实例化 PickTextMainWindow 类，创建主窗口
    myWin.show()  # 在桌面显示控件 myWin
    sys.exit(app.exec_())  # 结束进程，退出程序