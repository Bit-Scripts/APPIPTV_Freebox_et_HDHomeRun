"""A 16:9 TV viewport with a channel list layered over it."""
from PyQt6.QtCore import QSize, Qt, pyqtProperty
from PyQt6.QtWidgets import QWidget, QSizePolicy, QScrollArea, QFrame


class VideoArea(QWidget):
    def __init__(self, screen, sidebar, parent=None):
        super().__init__(parent)
        self.screen = screen
        self.sidebar = sidebar
        self._sidebar_width = 0
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet('VideoArea { background-color: black; }')
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        screen.setParent(self)
        sidebar.setParent(self)
        sidebar.setMinimumWidth(0)
        sidebar.hide()
        self.info_overlay = QScrollArea(self)
        self.info_overlay.setWidgetResizable(True)
        self.info_overlay.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.info_overlay.setFrameShape(QFrame.Shape.NoFrame)
        self.info_overlay.setStyleSheet('QScrollArea { background: transparent; }')
        self.info_overlay.viewport().setStyleSheet('background: transparent;')
        self.info_overlay.hide()

    def minimumSizeHint(self):
        return QSize(0, 0)

    def resizeEvent(self, event):
        self._position_children()
        super().resizeEvent(event)

    def _position_children(self):
        width = min(self.width(), self.height() * 16 // 9)
        height = min(self.height(), width * 9 // 16)
        self.screen.setGeometry((self.width() - width) // 2,
                                (self.height() - height) // 2, width, height)
        frame = self.screen.geometry()
        self.sidebar.setGeometry(frame.x(), frame.y(),
                                 min(self._sidebar_width, frame.width()), frame.height())
        self.sidebar.setVisible(self._sidebar_width > 0)
        self.info_overlay.setGeometry(frame.x(), frame.bottom() + 1 - min(220, frame.height()),
                                      frame.width(), min(220, frame.height()))
        if self.info_overlay.widget() is not None:
            self.info_overlay.raise_()
        self.sidebar.raise_()

    def set_info_widget(self, widget):
        self.info_overlay.setWidget(widget)
        self.info_overlay.show()
        self._position_children()

    def take_info_widget(self):
        self.info_overlay.hide()
        return self.info_overlay.takeWidget()

    @pyqtProperty(int)
    def sidebarWidth(self):
        return self._sidebar_width

    @sidebarWidth.setter
    def sidebarWidth(self, value):
        self._sidebar_width = max(0, value)
        self._position_children()
