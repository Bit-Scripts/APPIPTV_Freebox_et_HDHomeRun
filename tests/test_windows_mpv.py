import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from specs.fetch_windows_mpv import fetch, verify_x64_dll
from specs.verify_bundle import verify_names


def pe_header(machine=0x8664):
    data = bytearray(70)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 64)
    data[64:68] = b'PE\0\0'
    struct.pack_into('<H', data, 68, machine)
    return data


class WindowsMpvTest(unittest.TestCase):
    def test_wrong_hash_blocks_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'libmpv.7z').write_bytes(b'tampered')
            lock = root / 'lock.json'
            lock.write_text(json.dumps({'sha256': '0' * 64, 'library': 'libmpv-2.dll'}))
            with patch('specs.fetch_windows_mpv.subprocess.run') as extract:
                with self.assertRaisesRegex(ValueError, 'SHA-256'):
                    fetch(root, lock)
                extract.assert_not_called()

    def test_verified_archive_and_x64_library(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'libmpv.7z'
            archive.write_bytes(b'fixture')
            lock = root / 'lock.json'
            lock.write_text(json.dumps({'sha256': hashlib.sha256(b'fixture').hexdigest(),
                                        'library': 'libmpv-2.dll'}))
            library = root / 'libmpv-2.dll'
            library.write_bytes(pe_header())
            with patch('specs.fetch_windows_mpv.subprocess.run') as extract, \
                 patch('specs.fetch_windows_mpv.shutil.which', return_value='7z'):
                self.assertTrue(fetch(root, lock).samefile(library))
                extract.assert_called_once()
            library.write_bytes(pe_header(0x14c))
            with self.assertRaisesRegex(ValueError, 'x86_64'):
                verify_x64_dll(library)

    def test_bundle_contains_native_gl_and_correct_platform(self):
        samples = {'linux': ['libmpv.so.2', 'PyQt6/QtOpenGL.abi3.so',
                             'PyQt6/Qt6/plugins/platforms/libqwayland-generic.so'],
                   'win32': ['libmpv-2.dll', 'PyQt6/QtOpenGL.pyd',
                             'PyQt6/Qt6/plugins/platforms/qwindows.dll'],
                   'darwin': ['libmpv.2.dylib', 'QtOpenGL.framework/QtOpenGL',
                              'PyQt6/Qt6/plugins/platforms/libqcocoa.dylib']}
        for platform, names in samples.items():
            with self.subTest(platform=platform):
                self.assertTrue(all(verify_names(names, platform).values()))
                with self.assertRaisesRegex(ValueError, 'platform plugin'):
                    verify_names(names[:-1], platform)
