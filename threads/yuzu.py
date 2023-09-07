from PyQt6.QtCore import QThread, pyqtSignal
import os, requests, tempfile, uuid, subprocess, time, psutil

class YuzuLoader(QThread):
    finished = pyqtSignal(str, str, str)
    failed = pyqtSignal(str)

    def run(self):
        print('YuzuLoader started...')
        print('Fetching LocalAppData directory...')
        localappdata = os.environ.get('LOCALAPPDATA')
        if localappdata is None:
            self.failed.emit('Failed to find LocalAppData directory.<br>Please try again.')
            return
        print('Looking for maintenanceTool.exe...')
        maintenanceTool = os.path.join(localappdata, 'yuzu', 'maintenanceTool.exe')
        print('Looking for yuzu early access...')
        yuzuEA = os.path.join(localappdata, 'yuzu', 'yuzu-windows-msvc-early-access' ,'yuzu.exe')
        print('Looking for yuzu...')
        yuzu = os.path.join(localappdata, 'yuzu', 'yuzu-windows-msvc' ,'yuzu.exe')
        self.finished.emit(maintenanceTool, yuzuEA, yuzu)
        print('YuzuLoader finished!')

class YuzuInstaller(QThread):
    finished = pyqtSignal()
    failed = pyqtSignal(str)

    def run(self):
        print('YuzuInstaller started...')
        print('Fetching installer...')
        url = "https://api.github.com/repos/pineappleEA/liftinstall/releases/latest"
        try:
            res = requests.get(url)
        except Exception as e:
            self.failed.emit('Failed to establish a connection with the server.<br>Verify your internet connection and try again.')
            return
        if res.status_code != 200:
            self.failed.emit('Failed to fetch installer.<br>Please try again.')
            return
        try:
            url = res.json()['assets'][0]['browser_download_url']
        except Exception as e:
            self.failed.emit(f'Failed to fetch installer.<br>{e}')
            return
        print('Downloading installer...')
        installer = os.path.join(tempfile.gettempdir(), f'{uuid.uuid4()}.exe')
        try:
            res = requests.get(url)
            with open(installer, 'wb') as f:
                f.write(res.content)
        except Exception as e:
            self.failed.emit(f'Failed to download installer.<br>{e}')
            return
        print('Starting installer...')
        subprocess.Popen(f'"{installer}"')
        print('Waiting for installer to start...')
        time.sleep(5)
        while True:
            if any("maintenancetool" in p.info['name'] for p in psutil.process_iter(attrs=['name'])):
                break
            time.sleep(1)
        print('Waiting for installer to finish...')
        while True:
            if not any("maintenancetool" in p.info['name'] for p in psutil.process_iter(attrs=['name'])):
                break
            time.sleep(1)
        print('Deleting installer...')
        try:
            os.remove(installer)
        except Exception as e:
            self.failed.emit(f'Failed to delete installer.<br>{e}')
            return
        self.finished.emit()
        print('YuzuInstaller finished!')
