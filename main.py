import json
import os
import sys
import time
import platform
import logging
from logging.handlers import RotatingFileHandler
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication
import qdarkstyle
from src.MainWindow import MainWindow
from src.CustomSplashScreen import CustomSplashScreen

def configure_paths():
    application_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

    if getattr(sys, 'frozen', False):
        vlc_plugin_path = os.path.join(application_path, 'plugins')
        os.environ['VLC_PLUGIN_PATH'] = vlc_plugin_path

        if platform.system() == "Darwin":
            os.environ["LD_LIBRARY_PATH"] = os.path.join(application_path, 'lib')   
            os.environ['DYLD_LIBRARY_PATH'] = os.path.join(application_path, 'lib')
        else:
            os.environ["LD_LIBRARY_PATH"] = application_path
            
    else:
        vlc_plugin_path = {
            "Windows": 'C:\\Program Files\\VideoLAN\\VLC\\plugins',
            "Linux": '/usr/lib/x86_64-linux-gnu/vlc/plugins',
            "Darwin": '/Applications/VLC.app/Contents/MacOS/plugins'
        }

        vlc_lib_path = {
            "Darwin": '/Applications/VLC.app/Contents/MacOS/lib'
        }

        os_name = platform.system()
        if os_name in vlc_plugin_path:
            os.environ['VLC_PLUGIN_PATH'] = vlc_plugin_path[os_name]
            if os_name == "Darwin":
                os.environ['DYLD_LIBRARY_PATH'] = vlc_lib_path[os_name]

    return application_path

def configure_log_path():
    log_path = {
        "Windows": os.path.expanduser("~/AppData/Local/IPTVAPP/logs"),
        "Linux": os.path.expanduser("~/.local/share/IPTVAPP/logs"),
        "Darwin": os.path.expanduser("~/Library/Logs/IPTVAPP")
    }

    os_name = platform.system()
    log_directory = os.path.join(log_path.get(os_name, "/tmp"), 'Logs')

    try:
        os.makedirs(log_directory, exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create log directory: {str(e)}")
        sys.exit(1)

    return os.path.join(log_directory, 'application.log')

def setup_logging(log_filename):
    try:
        file_handler = RotatingFileHandler(log_filename, maxBytes=10**6, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logger.info("Logger configuration complete.")
    except Exception as e:
        print(f"Failed to configure logger: {str(e)}")
        sys.exit(1)

    return logger

def get_config_path(app_name):
    if os.name == 'nt':
        config_path = os.path.join(os.getenv('LOCALAPPDATA'), app_name)
    elif os.name == 'posix':
        home = os.path.expanduser('~')
        if sys.platform == 'darwin':
            config_path = os.path.join(home, 'Library', 'Application Support', app_name)
        else:
            config_path = os.path.join(home, '.local', 'share', app_name)
    else:
        raise Exception("Système d'exploitation non supporté")

    os.makedirs(config_path, exist_ok=True)
    return config_path

def load_config(config_file_path):
    default_config = {
        "hdhomerun_url": "http://hdhomerun.local/lineup.m3u",
        "auto_detect": True
    }
    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
            return {**default_config, **config}  # Utilise les valeurs par défaut pour les clés manquantes
    except (FileNotFoundError, json.JSONDecodeError):
        return default_config
    
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    
    splash_pix = QPixmap(os.path.join(application_path, './assets/image/splash_screen.png'))
    splash = CustomSplashScreen(splash_pix)
    splash.show()

    for i in range(1, 101):
        splash.setProgress(i)
        time.sleep(0.03)

    mainWindow = MainWindow(config, config_file_path, config_path, logger, application_path)
    mainWindow.show()
    splash.finish(mainWindow)

    sys.exit(app.exec())

if __name__ == '__main__':
    application_path = configure_paths()
    log_filename = configure_log_path()
    logger = setup_logging(log_filename)

    app_name = 'IPTVAPP'
    config_path = get_config_path(app_name)
    config_file_path = os.path.join(config_path, 'config.json')
    config = load_config(config_file_path)

    if platform.system() == "Linux":
        os.environ["QT_QPA_PLATFORM"] = "xcb"
        
    main()
