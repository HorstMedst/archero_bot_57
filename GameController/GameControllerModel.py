import os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal, QObject, QThread
from CaveDungeonEngine import CaveEngine, isConnected
import time
import threading


# import _thread
# from threading import Thread

class WorkerThread(threading.Thread):

    # Thread class with a _stop() method.
    # The thread itself has to check
    # regularly for the stopped() condition.

    def __init__(self, *args, **kwargs):
        super(WorkerThread, self).__init__(*args, **kwargs)
        self.function = None

    def run(self):
        self.function()


import enum


class EngineState(enum.Enum):
    Ready = 1
    Playing = 2
    StopInvoked = 3


class GameControllerModel(QObject):
    engineStatechanged = pyqtSignal(EngineState)
    connectionStateChanged = pyqtSignal(bool)
    resolutionChanged = pyqtSignal(str)
    dataFolderChanged = pyqtSignal(str)

    # onButtonLocationChanged = pyqtSignal(str)
    # onImageSelected = pyqtSignal()

    def __init__(self):
        super(QObject, self).__init__()
        # Default data
        self.engine = CaveEngine()
        self.dict_buttons = 'data.py'
        self.ch_images_path = "ui_chapters/"
        self.ch_image_ext = ".png"
        self.icon_path = "icons"
        self.icons_dataset = self.load_icons()
        self.currentEngineState: EngineState = EngineState.Ready
        self.connected = False
        self.chapters = ["1. Verdant Prairie",
                         "2. Storm Desert",
                         "3. Abandoned Dungeon",
                         "4. Crystal Mines",
                         "5. Lost Castle",
                         "6. Cave of Bones",
                         "7. Barens of Shadow",
                         "8. Silent Expanse",
                         "9. Frozen Pinnacle",
                         "10. Land of Doom",
                         "11. The Capital",
                         "12. Dungeon of Traps",
                         "13. Lava Land",
                         "14. Eskimo Lands"]
        self.workerThread: WorkerThread = None
        self.connectionStateChanged.connect(self.onconnectionStateChanged)
        self.startConnectionCheck()

    def onconnectionStateChanged(self, conn):
        if conn:
            self.engine.updateScreenSizeByPhone()

    def _changeConnectedstate(self, conn: bool):
        self.connected = conn
        self.connectionStateChanged.emit(conn)

    def _continousConnectionCheck(self):
        while True:
            c = isConnected()
            if c != self.connected:
                self._changeConnectedstate(c)
            time.sleep(10)

    def startConnectionCheck(self):
        self.connectionCheckThread = WorkerThread()
        self.connectionCheckThread.function = self._continousConnectionCheck
        self.connectionCheckThread.start()

    def load_data(self):
        pass

    def getLevelsNames(self):
        return self.engine.levels_type

    def load_icons(self):
        icons_dts = {}
        icons_dts['prev'] = "Start.png"
        icons_dts['play'] = "Play.png"
        icons_dts['pause'] = "Pause.png"
        icons_dts['next'] = "End.png"
        icons_dts['stop'] = "Stop.png"
        return icons_dts

    def getChapters(self) -> list:
        return self.chapters

    def getChapterImagePath(self, ch_number: int) -> str:
        return os.path.join(self.ch_images_path, "ch" + str(ch_number) + self.ch_image_ext)

    def getChNumberFromString(self, ch_str) -> int:
        for i, ch in enumerate(self.chapters):
            if ch == ch_str:
                return i + 1
        return -1

    def getIconPath(self, icon_name):
        if icon_name in self.icons_dataset.keys():
            path = os.path.join(self.icon_path, self.icons_dataset[icon_name])
        else:
            path = os.path.join(self.icon_path, "Error-Delete-Icon.png")
        return path

    def playDungeon(self):
        if self.workerThread is not None:
            self.stopDungeon()
        self.workerThread = WorkerThread()
        self.workerThread.function = self.engine.start_infinite_play
        self.workerThread.start()

    def waitForEngineEnd(self):
        if self.workerThread is not None:
            self.workerThread.join()

    def setEngineState(self, state: EngineState):
        self.currentEngineState = state
        self.engineStatechanged.emit(state)

    def _stopEngineUnsafe(self):
        try:
            self.engine.setStopRequested()
            self.waitForEngineEnd()
            self.workerThread = None
            self.setEngineState(EngineState.Ready)
        except Exception as e:
            print("Trying to kill process resulted in: %s" % str(e))

    def pauseDungeon(self):
        if self.workerThread is not None:
            try:
                self.setEngineState(EngineState.StopInvoked)
                new_thread = WorkerThread()
                new_thread.function = self._stopEngineUnsafe
                new_thread.start()
            except Exception as e:
                print("Trying to kill process resulted in: %s" % str(e))

    def stopDungeon(self):
        self.pauseDungeon()
        self.engine.changeCurrentLevel(0)
