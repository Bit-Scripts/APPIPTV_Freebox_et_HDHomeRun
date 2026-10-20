"""Check that each PyInstaller artifact contains libmpv and Qt's GL/platform files."""
import argparse
from pathlib import Path
import sys


def verify_names(names, platform):
    names = [name.lower().replace('\\', '/') for name in names]
    if platform == 'win32':
        native = any(name.rsplit('/', 1)[-1] in ('libmpv-2.dll', 'mpv-2.dll') for name in names)
        plugin = 'qwindows'
    elif platform == 'darwin':
        native = any('libmpv' in name and name.endswith('.dylib') for name in names)
        plugin = 'qcocoa'
    else:
        native = any('libmpv.so' in name for name in names)
        plugin = 'qwayland'
    checks = {'libmpv': native,
              'Qt OpenGL': any('opengl' in name and 'qt' in name for name in names),
              'Qt platform plugin': any('plugins/platforms/' in name and plugin in name for name in names)}
    missing = [name for name, found in checks.items() if not found]
    if missing:
        raise ValueError('Missing bundled files: ' + ', '.join(missing))
    return checks


def verify_bundle(bundle):
    bundle = Path(bundle)
    if bundle.is_dir():
        names = [str(file.relative_to(bundle)) for file in bundle.rglob('*') if file.is_file()]
        executable = (bundle / 'Contents/MacOS/APPIPTV' if bundle.suffix == '.app'
                      else bundle / 'APPIPTV')
    else:
        executable = bundle
        names = None
    from PyInstaller.archive.readers import CArchiveReader
    reader = CArchiveReader(str(executable))
    if names is None:
        names = list(reader.toc)
    checks = verify_names(names, sys.platform)
    pyz = next((name for name in reader.toc if name.startswith('PYZ')), None)
    if not pyz or 'mpv' not in reader.open_embedded_archive(pyz).toc:
        raise ValueError('Missing bundled python-mpv binding')
    checks['python-mpv'] = True
    return checks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle')
    print(verify_bundle(parser.parse_args().bundle))
