import os
import sys
import time
import random
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtWidgets, QtGui

# the menu will show as the system tray icon
class SysTrayIcon(QWidget):
    def __init__(self):
        sys.exit() if not loadImg() else lambda: None
        QtWidgets.QWidget.__init__(self)
        self._addPet = QAction("Add a pet", self, triggered = lambda: pets.append(Pet()))
        self._addPet.setIconVisibleInMenu(False)
        self._quit = QAction("Quit", self, triggered = qApp.quit)
        self._quit.setIconVisibleInMenu(False)
        self.pet = Pet()
        pets.append(self.pet)
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.setStyleSheet(
            "QMenu {"
            "   padding: 2px;"
            "   background-color: white;"
            "}"
            "QMenu::item {"
            "   background-color: rgb(50, 50, 50);"
            "   color: white;"
            "   padding: 5px 20px 5px 20px;"
            "}"
            "QMenu::separator {"
            "   height: 1px;"
            "   margin: 0px 0px 0px 0px;"
            "}"
            "QMenu::item:selected {"
            "   background-color: rgb(75, 75, 75);"
            "   color: white;"
            "}")
        self.trayIconMenu.addAction(self._addPet)
        # self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self._quit)
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon(os.path.join('.', IMGPATH, 'icon.ico')))
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.show()
    
class Pet(QWidget):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        self.img = QLabel(self)
        self.motion = 'idle_left' # current motion
        self.frame = 0 # current frame of current motion
        self.img.setPixmap(QPixmap.fromImage(motions[self.motion][self.frame]))

        # resize window to the specify size
        # here the image equal the window's size so named as img_size
        self.resize(img_size, img_size)
        self.move(int(0.7926 * QDesktopWidget().screenGeometry().width()),
                  int(0.7925 *  QDesktopWidget().screenGeometry().height()))
        self.show()

        self.dragging = False
        self.now_time = time.time()

        # there is the option called setFloor, that can set the pet on a specified floor
        # if isSetFloor is false then pet show as where it is
        self.floor = int(0.7925 *  QDesktopWidget().screenGeometry().height())
        self.isSetFloor = True

        # calculate the speed when dragging the pet
        self.prev_mouse_x = None
        self.prev_mouse_y = None
        self.velocity_x = None
        self.velocity_y = None

        # timer to that pet update their motion in the specified second
        self.timer = QTimer()
        self.timer.timeout.connect(self.runPet)
        self.timer.setSingleShot(True)
        self.timer.start(1)

        # when pet is falling after released by mouse, the fall_timer start
        self.fall_timer = QTimer()
        self.fall_timer.timeout.connect(self.falling)
        self.fall_timer.setSingleShot(True)

    def runPet(self):
        self.img.setPixmap(QPixmap.fromImage(motions[self.motion][self.frame]))
        # the pet cannot go beyond the screen
        if self.motion == 'walking_left':
            if self.geometry().x() - 3 < 0:
                # set the pet's position using setGeometry(x, y, w, h)
                # self.geometry().y() means pet's x position, as same as y
                self.setGeometry(0, self.geometry().y(), self.geometry().width(), self.geometry().height())
            else:
                self.setGeometry(self.geometry().x() - 3, self.geometry().y(), self.geometry().width(), self.geometry().height())
        if self.motion == 'walking_right':
            if self.geometry().x() + 3 + self.geometry().width() > QDesktopWidget().screenGeometry().width():
                self.setGeometry(QDesktopWidget().screenGeometry().width() - self.geometry().width(), self.geometry().y(), self.geometry().width(), self.geometry().height())
            else:
                self.setGeometry(self.geometry().x() + 3, self.geometry().y(), self.geometry().width(), self.geometry().height())

        if self.frame < len(motions[self.motion]) - 1:
            self.frame += 1
        else:
            self.frame = 0
            # try to select the next motion randomly
            self.motion = MOTION_CHANGE[self.motion][random.randrange(0, len(MOTION_CHANGE[self.motion]))]

        # update their motion in the specified second
        self.timer.start(MOTION_FRAME_INTERVAL[self.motion])

    def falling(self):
        # calculate their position by speed, and check if pet go beyond the screen
        if self.geometry().y() < self.floor:
            new_pos_x = self.geometry().x() + self.velocity_x * t
            if new_pos_x < 0:
                new_pos_x = 0
            elif new_pos_x + self.geometry().width() > QDesktopWidget().screenGeometry().width():
                new_pos_x = QDesktopWidget().screenGeometry().width() - self.geometry().width()
            new_pos_y = self.geometry().y() + self.velocity_y * t + (1 / 2) * gravity * t * t
            new_pos_y = self.floor if new_pos_y > self.floor else new_pos_y
            self.setGeometry(
                new_pos_x,
                new_pos_y,
                self.geometry().width(), 
                self.geometry().height()
            )
            self.velocity_y = self.velocity_y + gravity * t
            self.fall_timer.start(int(t * 1000))
        else:
            # the pet falled on the floor, start update motion again
            self.fall_timer.stop()
            self.prev_mouse_x, self.prev_mouse_y, self.velocity_x, self.velocity_y = None, None, None, None
            self.timer.start(1)

    def mousePressEvent(self, event):
        if self.fall_timer.isActive():
            self.fall_timer.stop()
        if event.button() == Qt.LeftButton:
            self.timer.stop()
            self.dragging = True
            self.m_w_dis = event.globalPos()-self.pos() # distance between position where mouse pressed and window's upper left position
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))
            
    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton and self.dragging:
            # globalPos() means the mouse's current position
            self.move(QMouseEvent.globalPos() - self.m_w_dis)
            QMouseEvent.accept()
            # calculate the speed of mouse (pet) in specified interval time
            if time.time() - self.now_time > t:
                self.now_time = time.time()
                self.velocity_x = (QMouseEvent.globalX() - self.prev_mouse_x) / t if self.prev_mouse_x != None else 0
                self.velocity_y = (QMouseEvent.globalY() - self.prev_mouse_y) / t if self.prev_mouse_y != None else 0
                self.prev_mouse_x, self.prev_mouse_y = QMouseEvent.globalX(), QMouseEvent.globalY()

            
    def mouseReleaseEvent(self, QMouseEvent):
        # if isSetFloor is false then pet show as where it is
        if not self.isSetFloor:
            self.floor = self.geometry().y()
        if Qt.LeftButton and self.dragging:
            self.dragging = False
            self.setCursor(QCursor(Qt.ArrowCursor))
            # start falling
            if self.geometry().y() < self.floor and self.isSetFloor:
                self.velocity_x, self.velocity_y = self.velocity_x / 15, self.velocity_y / 17
                self.fall_timer.start(1)
            else:
                self.prev_mouse_x, self.prev_mouse_y, self.velocity_x, self.velocity_y = None, None, None, None
                self.timer.start(1)

    # pop up menu when right click
    def contextMenuEvent(self, event):
        self._addPet = QAction("Add a pet", self, triggered = lambda: pets.append(Pet()))
        self._addPet.setIconVisibleInMenu(False)
        self._closePet = QAction("close this pet", self, triggered = self.closePet)
        self._closePet.setIconVisibleInMenu(False)
        if self.isSetFloor:
            self._setFloor = QAction("\u2705 set floor", self, triggered = self.setFloor)
        else:
            self._setFloor = QAction("set floor", self, triggered = self.setFloor)
        self._setFloor.setIconVisibleInMenu(False)
        self.popupMenu = QMenu(self)
        self.popupMenu.setStyleSheet(
            "QMenu {"
            "   padding: 2px;"
            "   background-color: white;"
            "}"
            "QMenu::item {"
            "   background-color: rgb(50, 50, 50);"
            "   color: white;"
            "   padding: 5px 20px 5px 20px;"
            "}"
            "QMenu::separator {"
            "   height: 1px;"
            "   margin: 0px 0px 0px 0px;"
            "}"
            "QMenu::item:selected {"
            "   background-color: rgb(75, 75, 75);"
            "   color: white;"
            "}")
        self.popupMenu.addAction(self._addPet)
        self.popupMenu.addAction(self._closePet)
        self.popupMenu.addAction(self._setFloor)

        self.popupMenu.popup(QCursor.pos())

    def closePet(self):
        if len(pets) == 1:
            sys.exit()
        else:
            self.close()
            for i, p in enumerate(pets):
                if id(p) == id(self):
                    del pets[i]
                    break
    
    def setFloor(self):
        self.isSetFloor = False if self.isSetFloor else True
        

def loadImg():
    load_success = True
    motions_path = {}
    for i in range(len(MOTION_NAME)):
        motions[MOTION_NAME[i]] = []
        motions_path[MOTION_NAME[i]] = os.path.join('.', IMGPATH, MOTION_NAME[i])
        for j in range(len(os.listdir(motions_path[MOTION_NAME[i]]))):
            if os.path.isfile(os.path.join(motions_path[MOTION_NAME[i]], str(j + 1) + '.png')):
                img = QImage()
                load_success |= img.load(os.path.join(motions_path[MOTION_NAME[i]], str(j + 1) + '.png'))
                img = img.scaled(img_size, img_size) # resized to the specified size
                motions[MOTION_NAME[i]].append(img)
    return load_success

if __name__ == '__main__':
    IMGPATH = 'image'
    MOTION_NAME = ['idle_left', 'idle_right', 'idle_to_sleep_left', 'idle_to_sleep_right',
                   'sleep_left', 'sleep_right', 'sleep_to_idle_left', 'sleep_to_idle_right',
                   'walking_left', 'walking_right']
    MOTION_CHANGE = {
        'idle_left': ['idle_left'] * 4 + ['idle_to_sleep_left'] * 1 + ['walking_left'] * 2 + ['walking_right'] * 2,
        'idle_right': ['idle_right'] * 4 + ['idle_to_sleep_right'] * 1 + ['walking_left'] * 2 + ['walking_right'] * 2,
        'idle_to_sleep_left': ['sleep_left'] * 1,
        'idle_to_sleep_right': ['sleep_right'] * 1,
        'sleep_left': ['sleep_left'] * 5 + ['sleep_to_idle_left'] * 1,
        'sleep_right': ['sleep_right'] * 5 + ['sleep_to_idle_right'] * 1,
        'sleep_to_idle_left': ['idle_left'] * 1,
        'sleep_to_idle_right': ['idle_right'] * 1,
        'walking_left': ['idle_left'] * 4 + ['idle_to_sleep_left'] * 1 + ['walking_left'] * 2 + ['walking_right'] * 2,
        'walking_right': ['idle_right'] * 4 + ['idle_to_sleep_right'] * 1 + ['walking_left'] * 2 + ['walking_right'] * 2,
    }
    MOTION_FRAME_INTERVAL = {
        'idle_left': 400,
        'idle_right': 400,
        'idle_to_sleep_left': 1000,
        'idle_to_sleep_right': 1000,
        'sleep_left': 1000,
        'sleep_right': 1000,
        'sleep_to_idle_left': 1000,
        'sleep_to_idle_right': 1000,
        'walking_left': 100,
        'walking_right': 100,
    }
    global pets, motions, img_size, t, gravity
    img_size = 200
    pets = []
    motions = {}
    t = 0.01
    gravity = 3000

    app = QApplication(sys.argv)
    sysTrayIcon = SysTrayIcon()
    sys.exit(app.exec_())
