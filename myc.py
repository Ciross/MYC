from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QComboBox, QCheckBox, QLabel, QMessageBox
from PyQt6.QtCore import Qt, QCoreApplication, QSettings, QSize, QTimer
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6 import uic
import sys, os, subprocess, time, psutil, requests
from threads.yuzu import YuzuLoader, YuzuInstaller
from threads.firmware import FirmwareLoader, FirmwareUpdater
from threads.keys import KeysLoader, KeysUpdater
from threads.utils import SettingsLoader, UpdateChecker

class MYC(QMainWindow):
    def __init__(self):
        super().__init__()
        self.version = '1.0.1'
        if getattr(sys, 'frozen', False):
            self.bundle_dir = sys._MEIPASS
        else:
            self.bundle_dir = os.path.dirname(os.path.abspath(__file__))
        uic.load_ui.loadUi(os.path.join(self.bundle_dir, 'ui/app.ui'), self)
        self.setWindowIcon(QIcon(os.path.join(self.bundle_dir, 'assets/icon.ico')))
        self.setFixedSize(QSize(252, 425))
        self.settings = QSettings('Ciross', 'MYC')
        try:
            self.myc = os.path.join(os.environ.get('LOCALAPPDATA'), 'MYC')
            if not os.path.exists(self.myc):
                os.mkdir(self.myc)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load local appdata.<br>{e}')
            sys.exit(0)
        self.credits = Credits()
        self.updateChecker = UpdateChecker(self.version)
        self.updateChecker.finished.connect(self.updateMYC)
        self.updating = False
        self.yuzuLoader = YuzuLoader()
        self.yuzuLoader.finished.connect(self.yuzuLoaded)
        self.yuzuLoader.failed.connect(self.yuzuNotLoaded)
        self.installer = YuzuInstaller()
        self.installer.finished.connect(self.yuzuInstalled)
        self.installer.failed.connect(self.yuzuNotInstalled)
        self.firmwareLoader = FirmwareLoader(self.myc)
        self.firmwareLoader.finished.connect(self.firmwareLoaded)
        self.keysLoader = KeysLoader()
        self.keysLoader.finished.connect(self.keysLoaded)
        self.firmwareUpdater = None
        self.keysUpdater = KeysUpdater(self.myc)
        self.keysUpdater.finished.connect(self.keysUpdated)
        self.keysUpdater.failed.connect(self.keysNotUpdated)
        self.autoStarter = False

        # --- Yuzu ---
        self.yuzuInstaller: QPushButton
        self.yuzuInstaller.clicked.connect(self.installYuzu)
        self.yuzuEA: QPushButton
        self.yuzu: QPushButton
        self.yuzuSelector: QComboBox
        self.autoStart: QCheckBox
        self.autoStart.stateChanged.connect(
            lambda: self.settings.setValue('autoStart', self.autoStart.isChecked()))
        # --- Firmware ---
        self.activeFirmwareValue: QLabel
        self.latestFirmwareValue: QLabel
        self.firmwareVersions: QComboBox
        self.updateFirmware: QPushButton
        self.updateFirmware.clicked.connect(self.updateTheFirmware)
        self.autoUpdateFirmware: QCheckBox
        self.autoUpdateFirmware.stateChanged.connect(
            lambda: self.settings.setValue('autoUpdateFirmware', self.autoUpdateFirmware.isChecked()))
        # --- Keys ---
        self.titleKeysValue: QLabel
        self.prodKeysValue: QLabel
        self.updateKeys: QPushButton
        self.updateKeys.clicked.connect(self.updateTheKeys)
        self.autoUpdateKeys: QCheckBox
        self.autoUpdateKeys.stateChanged.connect(
            lambda: self.settings.setValue('autoUpdateKeys', self.autoUpdateKeys.isChecked()))
        # --- Credits ---
        self.viewCredits: QPushButton
        self.viewCredits.clicked.connect(self.showCredits)

        QCoreApplication.processEvents()
        self.loadApp()

    def loadApp(self):
        self.updateChecker.start()
        self.yuzuLoader.start()
        self.firmwareLoader.start()
        self.keysLoader.start()
        self.settingsLoader = SettingsLoader(self.yuzuLoader, self.firmwareLoader, self.keysLoader)
        self.settingsLoader.finished.connect(self.loadSettings)
        self.settingsLoader.start()

    def loadSettings(self):
        self.yuzuInstaller.setEnabled(True)
        self.viewCredits.setEnabled(True)
        self.yuzuSelector.setCurrentIndex(self.settings.value('yuzu', 0))
        self.autoStart.setChecked(self.settings.value('autoStart', False, bool))
        if self.yuzuSelector.count() > 0:
            self.yuzuSelector.setEnabled(True)
            self.yuzuSelector.currentIndexChanged.connect(
                lambda: self.settings.setValue('yuzu', self.yuzuSelector.currentIndex()))
            self.autoStart.setEnabled(True)
        self.autoUpdateFirmware.setChecked(self.settings.value('autoUpdateFirmware', False, bool))
        self.autoUpdateFirmware.setEnabled(True)
        self.autoUpdateKeys.setChecked(self.settings.value('autoUpdateKeys', False, bool))
        self.autoUpdateKeys.setEnabled(True)
        if self.updating:
            return
        if self.autoStart.isChecked():
            self.autoStarter = True
        if self.autoUpdateKeys.isChecked():
            self.updateTheKeys()
        if self.autoUpdateFirmware.isChecked():
            self.updateTheFirmware()
        if self.autoStart.isChecked():
            while (self.keysUpdater != None and self.keysUpdater.isRunning()) or (self.firmwareUpdater != None and self.firmwareUpdater.isRunning()):
                time.sleep(1)
            self.timer = QTimer()
            self.countdown = 3
            self.timer.timeout.connect(self.autoStartYuzu)
            self.timer.start(1000)
            self.msgbox = QMessageBox()
            self.msgbox.setWindowModality(Qt.WindowModality.NonModal)
            self.msgbox.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            self.msgbox.setWindowIcon(QIcon(os.path.join(self.bundle_dir, 'assets/icon.ico')))
            self.msgbox.setWindowTitle('Auto-Start')
            self.msgbox.setText('MYC will launch yuzu in 3 seconds.<br>Press "Ctrl+C" to cancel.')
            self.msgbox.show()
            self.shortcut = QShortcut(QKeySequence('Ctrl+C'), self.msgbox)
            self.shortcut.activated.connect(self.cancelAutoStart)

    def askBox(self, title, text):
        box = QMessageBox()
        box.setWindowIcon(QIcon(os.path.join(self.bundle_dir, 'assets/icon.ico')))
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(title)
        box.setText(text)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        return box.exec() == QMessageBox.StandardButton.Yes
    
    def updateMYC(self, update):
        if not update:
            print('MYC is up to date!')
            return
        if not getattr(sys, 'frozen', False):
            QMessageBox.critical(self, 'Error', 'An update is available but MYC is not installed.<br>Please install MYC and try again.')
            return
        localappdata = os.environ.get('LOCALAPPDATA')
        if localappdata is None:
            QMessageBox.critical(self, 'Error', 'Failed to find LocalAppData directory.<br>Please try again.')
            return
        self.updating = True
        url = "https://api.github.com/repos/Ciross/MYC/releases/latest"
        print('Fetching latest version...')
        try:
            res = requests.get(url)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to establish a connection with the server.<br>Verify your internet connection and try again.<br>{e}')
            return
        if res.status_code != 200:
            QMessageBox.critical(self, 'Error', 'Failed to fetch latest version.<br>Please try again.')
            return
        try:
            print('Getting download url...')
            url = res.json()['assets'][0]['browser_download_url']
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to fetch download url.<br>{e}')
            return
        print('Downloading update...')
        try:
            res = requests.get(url)
            with open(os.path.join(localappdata, 'MYC', 'MYC-new.exe'), 'wb') as f:
                f.write(res.content)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to download update.<br>{e}')
            return
        print('Starting update...')
        if self.askBox('Update Available', 'MYC update is available.<br>Do you want to update now?'):
            app = os.path.abspath(sys.executable)
            new_app = os.path.join(localappdata, 'MYC', 'MYC-new.exe')
            updater = f"""@echo off
title MYC - Updater
echo Welcome to MYC - Updater
echo.
echo Waiting for MYC to close...
timeout /t 5 /nobreak

set OLD_APP_PATH={app}
set NEW_APP_PATH={new_app}

echo Deleting old application...
del %OLD_APP_PATH%

echo Moving new application to old application's location...
move %NEW_APP_PATH% %OLD_APP_PATH%

echo Update completed.
echo Starting new application...
start "" %OLD_APP_PATH%
"""
            with open(os.path.join(localappdata, 'MYC', 'MYC-updater.bat'), 'w') as f:
                f.write(updater)
            print('Starting updater...')
            subprocess.Popen(f'"{os.path.join(localappdata, "MYC", "MYC-updater.bat")}"')
            print('Closing MYC...')
            sys.exit(0)

    def autoStartYuzu(self):
        self.countdown -= 1
        if self.countdown == 0:
            self.timer.stop()
            self.start(self.yuzuSelector.currentData())

    def cancelAutoStart(self):
        self.autoStarter = False
        self.timer.stop()
        self.msgbox.close()
    
    def start(self, cmd):
        if any("yuzu" in p.info['name'] for p in psutil.process_iter(attrs=['name'])):
            QMessageBox.critical(self, 'Error', 'Yuzu is already running.<br>Please close yuzu and try again.')
            return
        subprocess.Popen(cmd, shell=True)
        sys.exit(0)

    def yuzuLoaded(self, maintenanceTool, yuzuEA, yuzu):
        self.yuzuSelector.clear()
        if os.path.exists(maintenanceTool):
            self.launcher = f'{maintenanceTool} --launcher'
        else:
            return
        if os.path.exists(yuzuEA):
            self.yuzuEA.setEnabled(True)
            self.yuzuEA.clicked.connect(
                lambda: self.start(f'{self.launcher} "{yuzuEA}"'))
            self.yuzuSelector.addItem('Yuzu EA', f'{self.launcher} "{yuzuEA}"')
        if os.path.exists(yuzu):
            self.yuzu.setEnabled(True)
            self.yuzu.clicked.connect(
                lambda: self.start(f'{self.launcher} "{yuzu}"'))
            self.yuzuSelector.addItem('Yuzu', f'{self.launcher} "{yuzu}"')

    def yuzuNotLoaded(self, error):
        QMessageBox.critical(self, 'Error', f'Failed to load Companion.<br>{error}')
        sys.exit(0)

    def firmwareLoaded(self, active, latest, versions):
        self.activeFirmwareValue.setText(active)
        self.latestFirmwareValue.setText(latest)
        for version, url in versions.items():
            self.firmwareVersions.addItem(version, url)
        if self.activeFirmwareValue.text() != 'Unknown':
            if active == latest:
                self.updateFirmware.setText('Firmware up to date!')
        if self.firmwareVersions.count() > 0:
            self.firmwareVersions.setEnabled(True)
            self.updateFirmware.setEnabled(True)

    def keysLoaded(self, titleKeys, prodKeys, newKeys):
        self.titleKeysValue.setText(titleKeys)
        self.prodKeysValue.setText(prodKeys)
        self.updateKeys.setEnabled(True)
        self.newKeys = 'Unknown'
        try:
            if newKeys != 'Unknown':
                self.newKeys = newKeys
                with open(os.path.join(self.myc, 'activeKeys.txt'), 'r') as f:
                    activeKeys = f.read().strip()
                if activeKeys == newKeys:
                    self.updateKeys.setText('Keys up to date!')
        except Exception as e:
            return

    def installYuzu(self):
        self.yuzuInstaller.setEnabled(False)
        self.yuzuInstaller.setText('Installing...')
        self.installer.start()

    def yuzuInstalled(self):
        self.yuzuInstaller.setEnabled(True)
        self.yuzuInstaller.setText('Yuzu Installer')
        self.yuzuLoader.start()
        QMessageBox.information(self, 'Success', 'Yuzu installed successfully.')

    def yuzuNotInstalled(self, error):
        self.yuzuInstaller.setEnabled(True)
        self.yuzuInstaller.setText('Yuzu Installer')
        QMessageBox.critical(self, 'Error', f'Failed to install Yuzu.<br>{error}')

    def updateTheFirmware(self):
        update = True
        if self.activeFirmwareValue.text() != 'Unknown':
            if self.activeFirmwareValue.text() == self.latestFirmwareValue.text():
                if self.autoStarter:
                    update = False
                else:
                    update = self.askBox('Update Firmware', 'Firmware is already up to date.<br>Do you want to update anyway?')
        if not update:
            return
        self.firmwareVersions.setEnabled(False)
        self.updateFirmware.setEnabled(False)
        self.updateFirmware.setText('Updating...')
        self.firmwareUpdater = FirmwareUpdater(self.myc, self.firmwareVersions.currentData(), self.firmwareVersions.currentText())
        self.firmwareUpdater.finished.connect(self.firmwareUpdated)
        self.firmwareUpdater.failed.connect(self.firmwareNotUpdated)
        self.firmwareUpdater.start()

    def firmwareUpdated(self, version):
        self.activeFirmwareValue.setText(version)
        self.firmwareVersions.setEnabled(True)
        self.updateFirmware.setEnabled(True)
        self.updateFirmware.setText('Firmware Updated!')
        if not self.autoStarter:
            QMessageBox.information(self, 'Success', f'Firmware updated successfully to {version}.')

    def firmwareNotUpdated(self, error):
        self.firmwareVersions.setEnabled(True)
        self.updateFirmware.setEnabled(True)
        self.updateFirmware.setText('Update Firmware')
        if not self.autoStarter:
            QMessageBox.critical(self, 'Error', f'Failed to update firmware.<br>{error}')

    def updateTheKeys(self):
        update = True
        try:
            if self.newKeys != 'Unknown':
                with open(os.path.join(self.myc, 'activeKeys.txt'), 'r') as f:
                    activeKeys = f.read().strip()
                if activeKeys == self.newKeys:
                    if self.autoStarter:
                        update = False
                    else:
                        update = self.askBox('Update Keys', 'Keys are already up to date.<br>Do you want to update anyway?')
        except Exception as e:
            pass
        if not update:
            return
        self.keysUpdater.start()
        self.updateKeys.setEnabled(False)
        self.updateKeys.setText('Updating...')

    def keysUpdated(self):
        self.keysLoader.start()
        self.updateKeys.setEnabled(True)
        self.updateKeys.setText('Keys Updated!')
        if not self.autoStarter:
            QMessageBox.information(self, 'Success', 'Keys updated successfully.')

    def keysNotUpdated(self, error):
        self.updateKeys.setEnabled(True)
        self.updateKeys.setText('Update Keys')
        if not self.autoStarter:
            QMessageBox.critical(self, 'Error', f'Failed to update keys.<br>{error}')

    def showCredits(self):
        if self.credits.isVisible():
            return
        self.credits.show()

    def closeEvent(self, event):
        self.credits.close()
        event.accept()

class Credits(QWidget):
    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            self.bundle_dir = sys._MEIPASS
        else:
            self.bundle_dir = os.path.dirname(os.path.abspath(__file__))
        uic.load_ui.loadUi(os.path.join(self.bundle_dir, 'ui/credits.ui'), self)
        self.setWindowIcon(QIcon(os.path.join(self.bundle_dir, 'assets/icon.ico')))
        self.setFixedSize(QSize(256, 153))
        # --- Credits ---
        self.cirossGithub: QPushButton
        self.cirossGithub.clicked.connect(lambda: self.openUrl('https://github.com/Ciross'))
        self.thzoriaGithub: QPushButton
        self.thzoriaGithub.clicked.connect(lambda: self.openUrl('https://github.com/THZoria'))
        self.pineappleeaGithub: QPushButton
        self.pineappleeaGithub.clicked.connect(lambda: self.openUrl('https://github.com/pineappleEA'))
        self.oxycoreDiscord: QPushButton
        self.oxycoreDiscord.clicked.connect(lambda: self.openUrl('https://discord.gg/tPYuvUEvJF'))

    def openUrl(self, url):
        subprocess.Popen(f'explorer "{url}"')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MYC()
    ex.show()
    try:
        sys.exit(app.exec())
    except SystemExit:
        print("Closing window...")
