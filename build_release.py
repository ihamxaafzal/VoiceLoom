"""Build a self-contained Windows x64 payload with a private Python runtime.

Run using a Python 3.12 x64 environment with the project requirements installed.
Build tools: PyInstaller 6.21+ and Inno Setup 6.7+. No runtime package installation.
"""
import argparse
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

def copy_tree(source, dest, excluded=()):
    shutil.copytree(source, dest, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', *excluded))

def build(args):
    source = Path(__file__).resolve().parent
    stage = Path(args.stage).resolve()
    stage.mkdir(parents=True, exist_ok=True)
    runtime = stage / 'runtime'
    runtime.mkdir(exist_ok=True)
    python_home = Path(sys.base_prefix)
    for pattern in ('python*.exe', 'python*.dll', 'vcruntime*.dll', 'LICENSE.txt'):
        for file in python_home.glob(pattern):
            shutil.copy2(file, runtime / file.name)
    for folder in ('DLLs', 'tcl'):
        copy_tree(python_home / folder, runtime / folder)
    copy_tree(python_home / 'Lib', runtime / 'Lib', ('site-packages', 'test', 'idlelib', 'ensurepip'))
    site = python_home / 'Lib' / 'site-packages'
    # This speech-only build environment has all language frontends installed.
    # Exclude development tools and optional torchaudio, whose binary ABI can differ.
    copy_tree(site, runtime / 'Lib' / 'site-packages',
              ('pip', 'pip-*.dist-info', 'PyInstaller', 'pyinstaller*.dist-info',
               '_pyinstaller_hooks_contrib', 'altgraph*', 'pefile*', 'peutils*',
               'pywin32_ctypes*', 'win32ctypes', 'torchaudio*'))
    (runtime / 'python312._pth').write_text('Lib\nDLLs\nLib/site-packages\nimport site\n', encoding='utf-8')
    app = stage / 'app'
    app.mkdir(exist_ok=True)
    for name in ('app.py', 'audio_engine.py', 'voice_catalog.py', 'english_voices.json',
                 'desktop_entry.py', 'installed_self_test.py'):
        shutil.copy2(source / name, app / name)
    copy_tree(source / 'assets', app / 'assets')
    copy_tree(Path(args.models), app / 'models')
    (app / 'bin').mkdir(exist_ok=True)
    shutil.copy2(args.ffmpeg, app / 'bin' / 'ffmpeg.exe')
    licenses = stage / 'ThirdPartyNotices'
    licenses.mkdir(exist_ok=True)
    for name in ('LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'FFMPEG-SOURCE.md'):
        document = source / name
        if not document.is_file():
            raise FileNotFoundError(f'Required release notice is missing: {document}')
        shutil.copy2(document, stage / name)
        shutil.copy2(document, licenses / name)
    shutil.copy2(python_home / 'LICENSE.txt', licenses / 'Python-LICENSE.txt')
    inventory = sorted([{'name': d.metadata['Name'], 'version': d.version,
                         'license': d.metadata.get('License-Expression') or d.metadata.get('License', ''),
                         'homepage': d.metadata.get('Home-page', '')}
                        for d in metadata.distributions(path=[str(runtime / 'Lib' / 'site-packages')])],
                       key=lambda x: x['name'].lower())
    (licenses / 'packages.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
                    '--windowed', '--noupx', '--name', 'VoiceLoom',
                    '--icon', str(source / 'assets' / 'voice-narrator.ico'),
                    '--distpath', str(stage), '--workpath', str(stage.parent / 'launcher-build'),
                    '--specpath', str(stage.parent), str(source / 'exe_launcher.py')], check=True)
    print('Payload ready:', stage, flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', required=True)
    parser.add_argument('--models', required=True, help='Kokoro snapshot with config, weights, voices')
    parser.add_argument('--ffmpeg', required=True)
    build(parser.parse_args())
