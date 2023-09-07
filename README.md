# <img src="/assets/icon.ico" width="35px" /> MYC - My Yuzu Companion
[Releases](https://github.com/Ciross/MYC/releases) <img src="https://img.shields.io/static/v1?label=license&message=Apache-2.0&color=white&style=flat" alt="License">

**MYC** (*My Yuzu Comapnion*) is an utility software that will helps you trough your Yuzu experience.  
 Helping you to install it trough an installer (with Yuzu Early Access available)

It will provide you **auto-updater** for the *firmware* and *keys*!  
 Also there's an **auto-starter** for your yuzu application, that will waits for updates before starting yuzu!  
 That mean, that you can start MYC instead of yuzu, he will update (if needed) and launch yuzu after!

Features
--------

- 🍋 **Yuzu Installer**  
 Install **Yuzu** nor **Yuzu Early Access** using the installer.

- ▶️ **Yuzu Starter**  
 Start your yuzu application using **MYC**.

- 🤖 **Auto-Starter**  
 Start your yuzu application automatically after launch, if auto updates are enabled,  
 it will wait for all updates to be done if any.

- 💾 **Firmware Updater (+ Auto-Updater)**  
 Update the firmware version version to the one you selected.  
 *Auto-Update will automatically download the latest firmware version.*

- 🔑 **Keys Updater (+ Auto-Updater)**  
 Update your keys to the latest keys available.
 *Auto-Update will automatically download the latest keys*

- 📄 **Credits**  
 View credits

Building
--------

How to build the source code?
- First you will need to install [**Python 3**](https://www.python.org/downloads/)  
  Make sure to add Python to PATH when downloading it!
- Then open a `cmd` or `powershell` in the project directory,  
  and install all depedencies by running this command

```bash
pip install -r requirements.txt
```

- If you don't want to build the application, at this point you can just run  

```bash
py myc.py
```

- Otherwise, if you want to build the application use

```bash
pyinstaller --add-data "assets/icon.ico;assets/" --add-data "ui/credits.ui;ui/" --add-data "ui/app.ui;ui/" --onefile --windowed --icon=assets/icon.ico --name=MYC myc.py
```

- Now you will find the builded `MYC.exe` in the `dist/` folder

Contributing
------------

Feel free to make push requests if you have any ideas!

License
-------

MYC is licensed under the Apache 2.0 License, which can be found in [LICENSE](LICENSE).
