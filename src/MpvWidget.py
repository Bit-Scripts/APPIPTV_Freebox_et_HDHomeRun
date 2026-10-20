"""libmpv rendering into Qt's framebuffer, including native Wayland surfaces."""
import logging
import locale
import ctypes

import mpv
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtOpenGLWidgets import QOpenGLWidget


class MpvWidget(QOpenGLWidget):
    error = pyqtSignal(str)
    playbackEnded = pyqtSignal()
    frameRequested = pyqtSignal()

    def __init__(self, logger=None, parent=None):
        super().__init__(parent)
        self.logger = logger or logging.getLogger(__name__)
        self._render = None
        self._closed = False
        self._pending_url = None
        self._gl_failed = False
        self._gl_functions = {}
        self._get_proc = mpv.MpvGlGetProcAddressFn(self._resolve_gl)
        self.frameRequested.connect(self.update, Qt.ConnectionType.QueuedConnection)
        # Use mpv's simple GL pipeline: advanced intermediate FBO rendering
        # produced intermittent black frames on the validated Mesa/Qt setup.
        # QApplication can reset LC_NUMERIC after python-mpv's import-time fix.
        # mpv_create requires C numeric formatting and may crash otherwise.
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.engine = mpv.MPV(
            vo='libmpv', keepaspect=True, gpu_dumb_mode=True, config=False, osc=False, input_default_bindings=False,
            input_vo_keyboard=False, idle=True, keep_open=False, volume=80,
            rtsp_transport='udp', demuxer_lavf_o='min_port=8784,max_port=8785',
            log_handler=self._log,
        )
        self.engine.register_event_callback(self._on_event)

    def _log(self, level, component, message):
        self.logger.log(logging.ERROR if level in ('error', 'fatal') else logging.DEBUG,
                        'mpv [%s] %s', component, message.rstrip())

    def _on_event(self, event):
        # Runs on mpv's event thread: only emit queued Qt signals here.
        if self._closed:
            return
        if event.event_id.value == mpv.MpvEventID.END_FILE:
            data = event.data
            if data.error < 0:
                self.error.emit('Flux indisponible (erreur mpv %s)' % data.error)
            elif data.reason == 0:  # EOF, not stop/replacement
                self.playbackEnded.emit()

    def _resolve_gl(self, _context, name):
        address = self.context().getProcAddress(name)
        return int(address) if address else 0

    def initializeGL(self):
        if self._closed:
            return
        try:
            self._gl_functions.clear()
            self._reset_gl_state()
            self._render = mpv.MpvRenderContext(
                self.engine, 'opengl', opengl_init_params={'get_proc_address': self._get_proc})
            self._render.update_cb = self._request_frame
            self.context().aboutToBeDestroyed.connect(self._release_gl,
                                                     Qt.ConnectionType.DirectConnection)
            if self._pending_url:
                url, self._pending_url = self._pending_url, None
                self.engine.play(url)
        except Exception as exc:
            self._gl_failed = True
            self.logger.exception('Initialisation OpenGL/libmpv impossible')
            self.error.emit('Initialisation OpenGL impossible : %s' % exc)

    def _request_frame(self):
        if not self._closed:
            self.frameRequested.emit()

    def _gl_function(self, name, result, *arguments):
        if name not in self._gl_functions:
            address = self._resolve_gl(None, name)
            if not address:
                raise RuntimeError('Fonction OpenGL absente : %s' % name.decode())
            self._gl_functions[name] = ctypes.CFUNCTYPE(result, *arguments)(address)
        return self._gl_functions[name]

    def _reset_gl_state(self):
        # Qt and mpv share a context. libmpv requires standard GL state.
        get_error = self._gl_function(b'glGetError', ctypes.c_uint)
        for _ in range(16):
            if not get_error():
                break
        pixel_store = self._gl_function(b'glPixelStorei', None, ctypes.c_uint, ctypes.c_int)
        for key, value in ((0x0CF5, 4), (0x0CF2, 0), (0x0CF3, 0), (0x0CF4, 0)):
            pixel_store(key, value)  # unpack alignment, row length and skips
        disable = self._gl_function(b'glDisable', None, ctypes.c_uint)
        for key in (0x0BE2, 0x0C11, 0x0B71, 0x0B90):
            disable(key)  # blend, scissor, depth, stencil
        color_mask = self._gl_function(b'glColorMask', None, *([ctypes.c_ubyte] * 4))
        color_mask(1, 1, 1, 1)
        bind_buffer = self._gl_function(b'glBindBuffer', None, ctypes.c_uint, ctypes.c_uint)
        bind_buffer(0x88EC, 0)  # GL_PIXEL_UNPACK_BUFFER

    def paintGL(self):
        if self._render is None or self._closed:
            return
        try:
            self._reset_gl_state()
            bind_fbo = self._gl_function(b'glBindFramebuffer', None, ctypes.c_uint, ctypes.c_uint)
            bind_fbo(0x8D40, self.defaultFramebufferObject())
            draw_buffer = self._gl_function(b'glDrawBuffer', None, ctypes.c_uint)
            draw_buffer(0x8CE0)  # GL_COLOR_ATTACHMENT0, not the window's GL_BACK
            ratio = self.devicePixelRatioF()
            self._render.render(flip_y=True, opengl_fbo={
                'fbo': self.defaultFramebufferObject(),
                'w': round(self.width() * ratio), 'h': round(self.height() * ratio)})
        except Exception as exc:
            self.logger.exception('Rendu libmpv impossible')
            self.error.emit('Erreur de rendu : %s' % exc)

    def play(self, url):
        if self._closed or self._gl_failed:
            raise RuntimeError('Le rendu OpenGL est indisponible')
        self.engine.pause = False
        if self._render is None:
            self._pending_url = url
        else:
            # loadfile replace serializes stream teardown before opening the next URL.
            self.engine.play(url)

    def set_paused(self, paused):
        self.engine.pause = bool(paused)

    def set_volume(self, value):
        self.engine.volume = max(0, min(100, value))

    def stop(self):
        self._pending_url = None
        if not self._closed:
            self.engine.stop()

    def _release_gl(self):
        if self._render is not None:
            self.makeCurrent()
            # Keep the ctypes callback alive until free has stopped mpv callbacks.
            self._render.free()
            self._render = None
            self.doneCurrent()

    def shutdown(self):
        if self._closed:
            return
        self._closed = True
        self._pending_url = None
        self._release_gl()  # Render context must be freed before mpv core.
        self.engine.terminate()
