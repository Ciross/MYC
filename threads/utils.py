from PyQt6.QtCore import QThread, pyqtSignal
import time, requests, os

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
    finished = pyqtSignal(bool)

    def __init__(self, version):
        super().__init__()
        self.version = version
        self.url = "https://api.github.com/repos/Ciross/MYC/releases/latest"

    def run(self):
        print('Looking for old updater...')
        try:
            localappdata = os.environ.get('LOCALAPPDATA')
            updater = os.path.join(localappdata, 'MYC', 'MYC-updater.bat')
            os.remove(updater)
            print('Old updater removed!')
        except Exception as e:
            print('No old updater found!')
        print('UpdateChecker started...')
        try:
            print('Fetching latest version...')
            res = requests.get(self.url)
        except Exception as e:
            print(f'Failed to establish a connection with the server. {e}')
            self.finished.emit(False)
            return
        if res.status_code != 200:
            print('Failed to fetch latest version.')
            self.finished.emit(False)
            return
        try:
            print('Comparing versions...')
            self.latest = res.json()['tag_name']
        except Exception as e:
            print(f'Failed to compare versions.{e}')
            self.finished.emit(False)
            return
        print('UpdateChecker finished!')
        self.finished.emit(self.version != self.latest)