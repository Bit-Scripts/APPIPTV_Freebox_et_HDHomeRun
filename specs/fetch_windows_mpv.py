"""Download the pinned Windows libmpv archive and verify it before extraction."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import urllib.request


def verify_archive(archive, expected):
    with Path(archive).open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != expected:
        raise ValueError('libmpv archive SHA-256 mismatch')


def verify_x64_dll(library):
    with Path(library).open('rb') as source:
        header = source.read(64)
        if len(header) != 64 or header[:2] != b'MZ':
            raise ValueError('libmpv is not a PE library')
        source.seek(struct.unpack_from('<I', header, 60)[0])
        if source.read(4) != b'PE\0\0' or source.read(2) != b'\x64\x86':
            raise ValueError('libmpv must be Windows x86_64')


def fetch(output, lock_file=None):
    lock = json.loads((Path(lock_file) if lock_file else
                       Path(__file__).with_name('windows-mpv.json')).read_text())
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / 'libmpv.7z'
    if not archive.exists():
        temporary = archive.with_suffix('.download')
        try:
            with urllib.request.urlopen(lock['url'], timeout=60) as source, temporary.open('wb') as target:
                shutil.copyfileobj(source, target)
            verify_archive(temporary, lock['sha256'])
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    verify_archive(archive, lock['sha256'])
    extractor = shutil.which('7z') or shutil.which('7zz')
    if not extractor:
        raise RuntimeError('7-Zip is required (7z or 7zz on PATH)')
    subprocess.run([extractor, 'x', '-y', '-o' + str(output), str(archive)],
                   check=True, stdout=subprocess.DEVNULL)
    library = output / lock['library']
    verify_x64_dll(library)
    return library


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(fetch(args.output))
