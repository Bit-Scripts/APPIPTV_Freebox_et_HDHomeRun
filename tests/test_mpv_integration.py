"""Real Qt/libmpv smoke test; run under a desktop session (Wayland preferred)."""
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import qdarkstyle

from PyQt6.QtCore import QEvent, QEventLoop, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QLabel
from src.MainWindow import MainWindow


def settle(ms=600):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


class PlayerIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))

    def test_render_controls_errors_and_shutdown(self):
        media = os.environ.get('IPTV_TEST_VIDEO')
        if not media:
            self.skipTest('Set IPTV_TEST_VIDEO to a red test video (see docs/mpv.md)')
        with tempfile.TemporaryDirectory() as config_dir, \
             patch.object(MainWindow, 'loadFreeboxPlaylist', return_value={
                 '2 - France 2': media, '3 - France 3': media}), \
             patch.object(MainWindow, 'get_ordered_uuids', return_value=[]), \
             patch.object(MainWindow, 'refresh_channel_logos'), \
             patch.object(MainWindow, 'get_uuid_of_current_channel') as epg:
            window = MainWindow({}, '', config_dir, logging.getLogger('test'),
                                str(Path(__file__).resolve().parents[1]))
            window.show()
            try:
                window.playStream(media, 'France 2')
                settle(1500)
                video = window.videoframe
                self.assertTrue(video.isValid())
                self.assertIsNotNone(video._render)
                for _ in range(20):
                    frame = video.grabFramebuffer()
                    color = frame.pixelColor(frame.width() // 2, frame.height() // 2)
                    if color.red() > 180:
                        break
                    settle(100)
                self.assertGreater(color.red(), 180)
                self.assertLess(color.green(), 70)
                window.resize(1000, 700)
                settle(200)
                resized = video.grabFramebuffer()
                self.assertGreater(resized.pixelColor(resized.width() // 2,
                                                      resized.height() // 2).red(), 180)
                self.assertEqual(video.engine.path, media)
                epg.assert_called_with('France 2')
                window.togglePlayPause()
                self.assertTrue(video.engine.pause)
                window.togglePlayPause()
                self.assertFalse(video.engine.pause)
                window.volumeSlider.setValue(37)
                self.assertEqual(video.engine.volume, 37)
                window.playStream(media, 'France 3')
                settle()
                self.assertIs(window.videoframe, video)
                self.assertEqual(window.current_channel_name, 'France 3')
                # Exercise the complete splitter/stack layout, including a URL
                # with no natural breaks and enough text to require scrolling.
                window.hover_enabled = False
                window.show_sidebar_animation.stop()
                window.hide_sidebar_animation.stop()
                sidebar = window.sidebar
                window.video_area.sidebarWidth = 300
                window.resize(1000, 700)
                settle(200)
                width_before = window.width()
                frame_before = window.stacked_widget.geometry()
                self.assertLessEqual(abs(frame_before.width() / frame_before.height() - 16 / 9), .01)
                # The hover event route drives the same overlay animations.
                window.eventFilter(window.video_area, QEvent(QEvent.Type.HoverLeave))
                settle(1100)
                self.assertEqual(window.video_area.sidebarWidth, 0)
                self.assertEqual(window.stacked_widget.geometry(), frame_before)
                window.enable_hover_detection()
                window.eventFilter(window.video_area, QEvent(QEvent.Type.HoverEnter))
                settle(200)
                self.assertEqual(window.video_area.sidebarWidth, 300)
                self.assertEqual(window.stacked_widget.geometry(), frame_before)
                preview = QPixmap(4, 4)
                preview.fill()
                with patch('src.SemiTransparentBlurWidget.ImageCache.get_pixmap', return_value=preview):
                    window.show_semitransparent_blur_widget(
                        'France 2', 'Programme actuel', 'Description détaillée. ' * 30,
                        'unused', window.get_channel_icon('France 2'), 1700000000,
                        3600, False, False, False)
                settle(200)
                self.assertEqual(window.stacked_widget.geometry(), frame_before)
                self.assertIs(window.video_area.info_overlay.widget(), window.semitransparent_widget)
                self.assertTrue(window.video_area.info_overlay.isVisible())
                self.assertFalse(window.semitransparent_widget.isWindow())
                self.assertEqual(window.width(), width_before)
                window.grab().save('/tmp/iptv-overlay-validated.png')
                window.remove_semibransparent_widget()
                self.assertFalse(window.video_area.info_overlay.isVisible())
                window.showError(" : " + "Erreur de lecture très détaillée. " * 30
                                 + "https://router/" + "x" * 3000)
                settle(200)
                self.assertEqual(window.width(), width_before)
                self.assertEqual(sidebar.width(), 300)
                label = window._channel_error_widget.findChild(QLabel, 'channelErrorText')
                self.assertTrue(label.wordWrap())
                self.assertGreater(label.heightForWidth(label.width()),
                                   label.fontMetrics().height())
                self.assertGreater(window._channel_error_widget.verticalScrollBar().maximum(), 0)
                self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
                self.assertEqual(window._channel_error_widget.horizontalScrollBar().maximum(), 0)
                window.resize(820, 620)
                settle(200)
                self.assertEqual(window.width(), 820)
                frame = window.stacked_widget.geometry()
                self.assertLessEqual(abs(frame.width() / frame.height() - 16 / 9), .01)
                self.assertEqual(sidebar.x(), frame.x())
                self.assertEqual(sidebar.y(), frame.y())
                self.assertEqual(sidebar.width(), 300)
                window.playStream(media, 'France 2')
                settle()
                self.assertIs(window.stacked_widget.currentWidget(), video)
                image = video.grabFramebuffer()
                self.assertGreater(image.pixelColor(image.width() // 2,
                                                    image.height() // 2).red(), 180)
                source_4_3 = os.environ.get('IPTV_TEST_4_3')
                if source_4_3:
                    window.resize(1400, 650)
                    settle(200)
                    frame = window.stacked_widget.geometry()
                    self.assertLessEqual(abs(frame.width() / frame.height() - 16 / 9), .01)
                    self.assertGreater(frame.x(), 0)
                    window.playStream(source_4_3, 'Source 4:3')
                    settle(800)
                    image = video.grabFramebuffer()
                    middle = image.pixelColor(image.width() // 2, image.height() // 2)
                    border = image.pixelColor(image.width() // 20, image.height() // 2)
                    self.assertGreater(middle.blue(), 180)
                    self.assertLess(border.blue(), 30)
                    # The blue source occupies 3/4 of the 16:9 frame width.
                    inner = image.pixelColor(image.width() // 5, image.height() // 2)
                    self.assertGreater(inner.blue(), 180)
                window.playStream('/nonexistent/iptv-test-missing.mp4', 'Missing')
                settle()
                self.assertIsNot(window.stacked_widget.currentWidget(), video)
                self.assertFalse(window.playPauseButton.isEnabled())
                window.playStream(media, 'France 2')
                settle()
                self.assertIs(window.stacked_widget.currentWidget(), video)
                self.assertTrue(window.isPlaying)
            finally:
                window.close()
                window.player.shutdown()  # Idempotent after close/aboutToQuit.
            self.assertIsNone(window.player._render)
            self.assertTrue(window.player._closed)
            print('Qt platform:', self.app.platformName())


if __name__ == '__main__':
    unittest.main()
