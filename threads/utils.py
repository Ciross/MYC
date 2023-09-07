from PyQt6.QtCore import QThread, pyqtSignal
import time

class SettingsLoader(QThread):
    finished = pyqtSignal()

    def __init__(self, yuzuLoader, firmwareLoader, keysLoader):
        super().__init__()
        self.yuzuLoader = yuzuLoader
        self.firmwareLoader = firmwareLoader
        self.keysLoader = keysLoader

    def run(self):
        print('SettingsLoader started...')
        while not self.yuzuLoader.isFinished() or not self.firmwareLoader.isFinished() or not self.keysLoader.isFinished():
            time.sleep(1)
        self.finished.emit()
        print('SettingsLoader finished!')

class UpdateChecker(QThread):
    pass