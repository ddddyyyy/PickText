#!/usr/bin/env python3
""" Take a screenshot and copy its text content to the clipboard. """

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPalette, QBrush
from PySide6.QtWidgets import QMainWindow

from display.display_main import Ui_MainWindow
from .logger import log_ocr_failure
from .ocr import get_ocr_result


class Snipper(QtWidgets.QWidget):
    def __init__(self, parent, langs=None):
        super().__init__(parent=parent)

        self.setWindowTitle("TextShot")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.ToolTip
            | Qt.WindowType.Popup
        )
        # self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos())

        self.setGeometry(self._screen.geometry())

        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.getWindow()))
        self.setPalette(palette)

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.start, self.end = QtCore.QPoint(), QtCore.QPoint()
        self.langs = langs

    def getWindow(self):
        return self._screen.grabWindow(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QtWidgets.QApplication.quit()

        return super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 100))
        painter.drawRect(0, 0, self.width(), self.height())

        if self.start == self.end:
            return super().paintEvent(event)

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
        painter.setBrush(painter.background())
        painter.drawRect(QtCore.QRect(self.start, self.end))
        return super().paintEvent(event)

    def mousePressEvent(self, event):
        self.start = self.end = event.pos()
        self.update()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()
        return super().mouseMoveEvent(event)

    def snipOcr(self):
        ocr_result = self.ocrOfDrawnRectangle()
        if ocr_result:
            return ocr_result
        else:
            log_ocr_failure()

    def hide(self):
        print('now is hide')
        super().hide()
        # 重置鼠标样式
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.processEvents()

    def ocrOfDrawnRectangle(self):
        return get_ocr_result(
            self.getWindow().copy(
                min(self.start.x(), self.end.x()),
                min(self.start.y(), self.end.y()),
                abs(self.start.x() - self.end.x()),
                abs(self.start.y() - self.end.y()),
            ),
            self.langs,
        )


class OneTimeSnipper(Snipper):
    """Take an OCR screenshot once then end execution."""

    def mouseReleaseEvent(self, event):
        if self.start == self.end:
            return super().mouseReleaseEvent(event)
        # 隐藏截图组件
        self.hide()


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
        self.prevShot = None
        self.timer.timeout.connect(self.onShotOcrInterval)

    def mouseReleaseEvent(self, event):
        if self.start == self.end:
            return super().mouseReleaseEvent(event)
        # Take a shot as soon as the rectangle has been drawn
        self.onShotOcrInterval()
        # self.togglePause()
        # 隐藏截图组件
        self.hide()

    def onShotOcrInterval(self):
        self.prevShot = self.getWindow().copy(
            min(self.start.x(), self.end.x()),
            min(self.start.y(), self.end.y()),
            abs(self.start.x() - self.end.x()),
            abs(self.start.y() - self.end.y()),
        )
        palette = QPalette(self.myWin.ScreenShotDisplay.palette())
        palette.setBrush(QPalette.ColorRole.Window, QBrush(
            self.prevShot.scaled(self.myWin.ScreenShotDisplay.width(), self.myWin.ScreenShotDisplay.height(),
                                 Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                 Qt.TransformationMode.SmoothTransformation)))
        self.myWin.ScreenShotDisplay.setPalette(palette)
        self.myWin.ScreenShotDisplay.setAutoFillBackground(True)

    def togglePause(self):
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

    def resizeEvent(self, event):
        print('resize the frame')
        # 如果窗口大小改变，重新绘制背景图
        if self.snipper and self.snipper.prevShot:
            palette = QPalette(self.ScreenShotDisplay.palette())
            palette.setBrush(QPalette.ColorRole.Window, QBrush(
                self.snipper.prevShot.scaled(self.ScreenShotDisplay.width(), self.ScreenShotDisplay.height(),
                                             Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                             Qt.TransformationMode.SmoothTransformation)))
            self.ScreenShotDisplay.setPalette(palette)
            self.ScreenShotDisplay.setAutoFillBackground(True)

    def clickButton(self):
        self.snipper = IntervalSnipper(self, 500, None)
        self.snipper.show()
