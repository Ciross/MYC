from PyQt6.QtCore import QThread, pyqtSignal
import os, requests, uuid, tempfile, zipfile

class KeysLoader(QThread):
    finished = pyqtSignal(str, str, str)

    def run(self):
        print('KeysLoader started...')
        print('Fetching AppData directory...')
        appdata = os.environ.get('APPDATA')
        if appdata is None:
            self.finished.emit('Unknown', 'Unknown')
            return
        print('Looking for title.keys...')
        titleKeys = os.path.join(appdata, 'yuzu', 'keys', 'title.keys')
        print('Looking for prod.keys...')
        prodKeys = os.path.join(appdata, 'yuzu', 'keys', 'prod.keys')
        if not os.path.exists(titleKeys):
            titleKeys = 'Unknown'
        else:
            titleKeys = self.getSize(os.path.getsize(titleKeys))
        if not os.path.exists(prodKeys):
            prodKeys = 'Unknown'
        else:
            prodKeys = self.getSize(os.path.getsize(prodKeys))
        print('Check for new keys...')
        url = "https://cdn.discordapp.com/attachments/1132786648397140179/1132786648732672060/keys.zip"
        try:
            res = requests.head(url)
        except Exception as e:
            self.finished.emit(titleKeys, prodKeys, 'Unknown')
            return
        if res.status_code != 200:
            self.finished.emit(titleKeys, prodKeys, 'Unknown')
            return
        newKeys = res.headers['last-modified']
        self.finished.emit(titleKeys, prodKeys, newKeys)
        print('KeysLoader finished!')

    
    def getSize(self, size):
        for unit in ['o', 'Ko', 'Mo', 'Go', 'To']:
            if size < 1000.0:
                break
            size /= 1000.0
        return f"{size:.0f} {unit}"
    
class KeysUpdater(QThread):
    finished = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, myc_dir):
        super().__init__()
        self.myc_dir = myc_dir

    def run(self):
        print('KeysUpdater started...')
        url = "https://cdn.discordapp.com/attachments/1132786648397140179/1132786648732672060/keys.zip"
        print('Preparing keys directory...')
        appdata = os.environ.get('APPDATA')
        if appdata is None:
            self.failed.emit('Failed to find AppData directory.<br>Please try again.')
            return
        keysDir = os.path.join(appdata, 'yuzu', 'keys')
        if not os.path.exists(keysDir):
            self.failed.emit('Failed to find keys directory.<br>Please try again.')
            return
        print('Downloading keys...')
        keys = os.path.join(tempfile.gettempdir(), f'{uuid.uuid4()}.zip')
        try:
            res = requests.get(url)
        except Exception as e:
            self.failed.emit('Failed to establish connection with server.<br>Verify your internet connection and try again.')
            return
        try:
            with open(keys, 'wb') as f:
                f.write(res.content)
        except Exception as e:
            self.failed.emit(f'Failed to download keys.<br>{e}')
            return
        print('Cleaning keys directory...')
        for file in os.listdir(keysDir):
            if file.endswith('.keys'):
                os.remove(os.path.join(keysDir, file))
        print('Extracting keys...')
        try:
            with zipfile.ZipFile(keys, 'r') as zip_ref:
                zip_ref.extractall(keysDir)
        except Exception as e:
            os.remove(keys)
            self.failed.emit(f'Failed to extract keys.<br>{e}')
            return
        print('Deleting keys...')
        try:
            os.remove(keys)
        except Exception as e:
            self.failed.emit(f'Failed to delete keys.<br>{e}')
            return
        self.finished.emit()
        print('Saving active keys...')
        try:
            res = requests.head(url)
            with open(os.path.join(self.myc_dir, 'activeKeys.txt'), 'w') as f:
                f.write(res.headers['last-modified'])
        except Exception as e:
            self.failed.emit(f'Failed to save active keys.<br>{e}')
            return
        print('KeysUpdater finished!')


