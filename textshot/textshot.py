#!/usr/bin/env python3
""" Take a screenshot and copy its text content to the clipboard. """
from PyQt5.QtGui import QCursor
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMainWindow, QGraphicsPixmapItem, QGraphicsScene

from display.display_main import Ui_MainWindow


class Snipper(QtWidgets.QWidget):
    def __init__(self, parent, langs=None):
        super().__init__(parent=parent)

        self.setWindowTitle("TextShot")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.ToolTip
            | Qt.WindowType.Popup
        )
        # mac系统设置全屏，会导致直接切换到另外一个屏幕
        # self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos())

        self.setGeometry(self._screen.geometry())

        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.get_window()))
        self.setPalette(palette)

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.start, self.end = QtCore.QPoint(), QtCore.QPoint()
        self.langs = langs
        self.prevShot = None

    def get_window(self):
        return self._screen.grabWindow(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QtWidgets.QApplication.quit()

        return super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 100))
        painter.drawRect(self.rect())

        if self.start == self.end:
            return super().paintEvent(event)

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
        painter.setBrush(painter.background())
        painter.drawRect(QtCore.QRect(self.start, self.end))
        return super().paintEvent(event)

    def mousePressEvent(self, event):
        self.start = self.end = event.position().toPoint()
        self.update()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.end = event.position().toPoint()
        self.update()
        return super().mouseMoveEvent(event)

    def get_screen_shot_img(self):
        # 获取设备像素比率  物理像素与逻辑像素之间的比率
        device_pixel_ratio = self._screen.devicePixelRatio()
        # 计算实际绘制尺寸
        # 在显示和编程的时候，是按照逻辑像素取进行展示与设计
        # 逻辑尺寸= 物理尺寸 / 像素比  计算出符合当前屏幕的尺寸
        # 此处截图的时候，也要记得调整一下 从逻辑像素转换成为物理像素进行抓取
        # 不然截图出来会有偏差
        # 物理像素 = 逻辑像素 * 像素比率
        real_start = QtCore.QPoint()
        real_end = QtCore.QPoint()
        real_start.setX(int(self.start.x() * device_pixel_ratio))
        real_start.setY(int(self.start.y() * device_pixel_ratio))
        real_end.setX(int(self.end.x() * device_pixel_ratio))
        real_end.setY(int(self.end.y() * device_pixel_ratio))
        rect = QtCore.QRect(real_start, real_end)
        return self.get_window().copy(rect)

    def hide(self):
        print('now is hide')
        super().hide()
        # 重置鼠标样式
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.processEvents()

class IntervalSnipper(Snipper):
    """
    Draw the screenshot rectangle once, then perform OCR there every `interval`
    ms.
    """

    prevOcrResult = None

    def __init__(self, parent, interval, langs=None):
        super().__init__(parent, langs)
        self.interval = interval
        self.myWin: PickTextMainWindow = parent

        # 配置定时组件
        self.timer = QTimer()
        self.is_paused = True
        self.timer.timeout.connect(self.on_shot_ocr_interval)

    def mouseReleaseEvent(self, event):
        if self.start == self.end:
            return super().mouseReleaseEvent(event)
        # Take a shot as soon as the rectangle has been drawn
        self.on_shot_ocr_interval()
        # 隐藏截图组件
        self.hide()

    def on_shot_ocr_interval(self):
        self.prevShot = self.get_screen_shot_img()
        # put the img into scene
        item = QGraphicsPixmapItem(self.prevShot)
        scene = QGraphicsScene()
        scene.addItem(item)
        self.myWin.ScreenShotDisplay.setScene(scene)

    def toggle_pause(self):
        if self.is_paused:
            self.timer.start(self.interval)
        else:
            self.timer.stop()
        self.is_paused = not self.is_paused


class PickTextMainWindow(QMainWindow, Ui_MainWindow):  # 继承 QMainWindow 类和 Ui_MainWindow 界面类
    class PickTextMainWindow(QMainWindow, Ui_MainWindow):
        """
        Main window class for the PickText application.
        """

    def __init__(self, parent=None):
        super(PickTextMainWindow, self).__init__(parent)  # 初始化父类
        self.setupUi(self)  # 继承 Ui_MainWindow 界面类
        self.snipper = None
        self.toolButton_3.clicked.connect(self.clickButton)

    def clickButton(self):
        if self.snipper:
            self.snipper.close()
            self.snipper.deleteLater()
        self.snipper = IntervalSnipper(self, 500, None)
        self.snipper.show()
