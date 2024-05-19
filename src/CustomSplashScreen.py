from PyQt6.QtWidgets import QProgressBar, QSplashScreen, QApplication

class CustomSplashScreen(QSplashScreen):
    def __init__(self, pixmap, *args, **kwargs):
        super(CustomSplashScreen, self).__init__(pixmap, *args, **kwargs)
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(100, 350, 500, 20)  # Ajuster la position et la taille

    def setProgress(self, value):
        self.progressBar.setValue(value)
        QApplication.instance().processEvents()