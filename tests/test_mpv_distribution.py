import ctypes.util
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from specs.mpv_build import build_inputs


class DistributionTest(unittest.TestCase):
    def test_build_requires_library_and_includes_runtime_hook(self):
        with patch.dict(os.environ, {'IPTV_LIBMPV': '/nonexistent/mpv.so'}):
            with self.assertRaises(RuntimeError):
                build_inputs('specs')
        with tempfile.TemporaryDirectory() as folder:
            library = Path(folder) / 'libmpv.so.2'
            library.touch()
            with patch.dict(os.environ, {'IPTV_LIBMPV': str(library)}):
                inputs = build_inputs('specs')
            self.assertIn('mpv', inputs['hiddenimports'])
            self.assertTrue(Path(inputs['scripts'][0]).is_file())
            self.assertTrue(Path(inputs['runtime_hooks'][0]).is_file())

    def test_frozen_resolution_preserves_other_libraries(self):
        with tempfile.TemporaryDirectory() as folder:
            library = Path(folder) / 'libmpv.so.2.5.0'
            library.touch()
            with patch.object(sys, 'frozen', True, create=True), \
                 patch.object(sys, '_MEIPASS', folder, create=True), \
                 patch.object(ctypes.util, 'find_library', return_value='original'):
                runpy.run_path('specs/mpv_runtime_hook.py')
                self.assertEqual(ctypes.util.find_library('mpv'), str(library))
                self.assertEqual(ctypes.util.find_library('EGL'), 'original')


    def test_all_three_specs_include_native_library_and_qt_gl(self):
        with tempfile.TemporaryDirectory() as folder:
            library = Path(folder) / 'libmpv.so.2'
            library.touch()
            for platform in ('linux', 'windows', 'macos'):
                with self.subTest(platform=platform), patch.dict(os.environ, {'IPTV_LIBMPV': str(library)}):
                    analysis = SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])
                    with patch('builtins.print'):
                        captured = []
                        def analyze(*args, **kwargs):
                            captured.append(kwargs)
                            return analysis
                        runpy.run_path('specs/main-' + platform + '.spec', init_globals={
                            'SPECPATH': str(Path('specs').resolve()), 'Analysis': analyze,
                            'PYZ': lambda *a, **kw: None, 'EXE': lambda *a, **kw: None,
                            'COLLECT': lambda *a, **kw: None, 'BUNDLE': lambda *a, **kw: None})
                    self.assertEqual(captured[0]['binaries'], [(str(library), '.')])
                    self.assertIn('PyQt6.QtOpenGLWidgets', captured[0]['hiddenimports'])
                    self.assertTrue(captured[0]['runtime_hooks'][0].endswith('mpv_runtime_hook.py'))
