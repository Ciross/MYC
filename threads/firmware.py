from PyQt6.QtCore import QThread, pyqtSignal
import os, requests, uuid, tempfile, shutil, zipfile

class FirmwareLoader(QThread):
    finished = pyqtSignal(str, str, dict)

    def __init__(self, myc_dir):
        super().__init__()
        self.myc_dir = myc_dir

    def run(self):
        print('FirmwareLoader started...')
        self.finished.emit(self.getActiveFirmware(), self.getLatestFirmware(), self.getFirmwareVersions())
        print('FirmwareLoader finished!')

    def getActiveFirmware(self):
        try:
            with open(os.path.join(self.myc_dir, 'activeFirmware.txt'), 'r') as f:
                return f.read().strip()
        except Exception as e:
            return 'Unknown'

    def getLatestFirmware(self):
        url = "https://api.github.com/repos/THZoria/NX_Firmware/releases/latest"
        try:
            res = requests.get(url)
        except Exception as e:
            return 'Unknown'
        if res.status_code != 200:
            return 'Unknown'
        try:
            return res.json()['tag_name']
        except Exception as e:
            return 'Unknown'

    def getFirmwareVersions(self):
        url = "https://api.github.com/repos/THZoria/NX_Firmware/releases"
        try:
            res = requests.get(url)
        except Exception as e:
            return {"Unknown": None}
        if res.status_code != 200:
            return {"Unknown": None}
        try:
            versions = {}
            for version in res.json():
                versions[version['tag_name']] = version['assets'][0]['browser_download_url']
            return versions
        except Exception as e:
            return {"Unknown": None}
        
class FirmwareUpdater(QThread):
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, myc_dir, url, version):
        super().__init__()
        self.myc_dir = myc_dir
        self.url = url
        self.version = version

    def run(self):
        print('FirmwareUpdater started...')
        if self.url is None or self.version == 'Unknown':
            self.failed.emit('No download url provided.')
            return
        print('Preparing firmware directory...')
        appdata = os.environ.get('APPDATA')
        if appdata is None:
            self.failed.emit('Failed to find AppData directory.<br>Please try again.')
            return
        firmwareDir = os.path.join(appdata, 'yuzu', 'nand', 'system', 'Contents', 'registered')
        if not os.path.exists(firmwareDir):
            self.failed.emit('Failed to find firmware directory.<br>Please try again.')
            return
        print('Downloading firmware...')
        firmware = os.path.join(tempfile.gettempdir(), f'{uuid.uuid4()}.zip')
        try:
            res = requests.get(self.url)
            with open(firmware, 'wb') as f:
                f.write(res.content)
        except Exception as e:
            self.failed.emit(f'Failed to download firmware.<br>{e}')
            return
        print('Cleaning firmware directory...')
        try:
            for file in os.listdir(firmwareDir):
                path = os.path.join(firmwareDir, file)
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
        except Exception as e:
            os.remove(firmware)
            self.failed.emit(f'Failed to clean firmware directory.<br>{e}')
            return
        print('Extracting firmware...')
        try:
            with zipfile.ZipFile(firmware, 'r') as zip_ref:
                zip_ref.extractall(firmwareDir)
        except Exception as e:
            os.remove(firmware)
            self.failed.emit(f'Failed to extract firmware.<br>{e}')
            return
        print('Deleting firmware...')
        try:
            os.remove(firmware)
        except Exception as e:
            self.failed.emit(f'Failed to delete firmware.<br>{e}')
            return
        print('Saving active firmware...')
        try:
            with open(os.path.join(self.myc_dir, 'activeFirmware.txt'), 'w') as f:
                f.write(self.version)
        except Exception as e:
            self.failed.emit(f'Failed to save active firmware.<br>{e}')
            return
        self.finished.emit(self.version)
        print('FirmwareUpdater finished!')
