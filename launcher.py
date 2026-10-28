"""Portable startup checks and persistent laptop diagnostics."""
import importlib.util
import os
from pathlib import Path
import platform
import runpy
import struct
import subprocess
import sys
import traceback
from datetime import datetime

BASE = Path(__file__).resolve().parent
REQUIRED = ('app.py', 'audio_engine.py', 'voice_catalog.py', 'english_voices.json')
MODULES = ('tkinter', 'numpy', 'scipy', 'soundfile', 'sounddevice', 'torch', 'kokoro', 'edge_tts')


class Tee:
    def __init__(self, console, logfile):
        self.console, self.logfile = console, logfile

    def write(self, text):
        self.logfile.write(text)
        self.logfile.flush()
        if self.console:
            try:
                self.console.write(text)
                self.console.flush()
            except (OSError, UnicodeError):
                pass
        return len(text)

    def flush(self):
        self.logfile.flush()
        if self.console:
            self.console.flush()

    def isatty(self):
        return False


def preflight():
    if not (3, 10) <= sys.version_info < (3, 13) or struct.calcsize('P') != 8:
        raise RuntimeError('Use Python 3.10-3.12 64-bit. Python 3.12 is recommended.')
    missing = [name for name in REQUIRED if not (BASE/name).is_file()]
    if missing:
        raise RuntimeError('Project files missing: '+', '.join(missing)+'. Copy the whole project folder.')
    missing = [name for name in MODULES if importlib.util.find_spec(name) is None]
    if missing:
        raise RuntimeError('Missing packages: '+', '.join(missing)+'. Run setup.bat on this computer.')


def diagnose():
    print('Platform:', platform.platform())
    print('Python:', sys.version.replace('\n', ' '))
    print('Architecture:', struct.calcsize('P')*8, 'bit')
    print('Project:', BASE)
    print('Virtual environment:', sys.prefix != sys.base_prefix)
    for name in REQUIRED:
        print('File:', name, 'OK' if (BASE/name).is_file() else 'MISSING')
    success = all((BASE/name).is_file() for name in REQUIRED)
    for module in MODULES:
        try:
            result = subprocess.run([sys.executable, '-c',
                f"import {module}; print(getattr({module}, '__version__', 'import OK'))"],
                capture_output=True, text=True, errors='replace', timeout=90,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            print(f'\n{module}: '+('OK' if result.returncode == 0 else f'FAILED (exit {result.returncode})'))
            print(result.stdout.strip())
            if result.returncode:
                success = False
                print(result.stderr.strip()[-5000:])
        except (OSError, subprocess.TimeoutExpired) as exc:
            success = False
            print(module, 'FAILED:', exc)
    print('\nResult:', 'Dependency imports passed.' if success else 'Problems found. Run setup.bat and review logs/setup.log.')
    return 0 if success else 1


def main():
    mode = 'diagnostic' if '--diagnose' in sys.argv else 'startup'
    try:
        folder = BASE/'logs'
        folder.mkdir(exist_ok=True)
    except OSError:
        folder = Path(os.environ.get('LOCALAPPDATA', str(Path.home())))/'VoiceLoom'/'logs'
        folder.mkdir(parents=True, exist_ok=True)
    path = folder/(mode+'.log')
    logfile = path.open('a', encoding='utf-8', buffering=1)
    sys.stdout, sys.stderr = Tee(sys.stdout, logfile), Tee(sys.stderr, logfile)
    print('\n===', datetime.now().isoformat(timespec='seconds'), '===')
    print('Log:', path)
    print('Python:', sys.executable)
    try:
        if '--diagnose' in sys.argv:
            return diagnose()
        preflight()
        if '--check' in sys.argv:
            for module in MODULES:
                __import__(module)
            print('Startup dependencies imported successfully.')
            return 0
        os.chdir(BASE)
        sys.argv = [str(BASE/'app.py')]+sys.argv[1:]
        runpy.run_path(str(BASE/'app.py'), run_name='__main__')
        return 0
    except Exception as exc:
        traceback.print_exc()
        message = f'{exc}\n\nRun setup.bat on this computer.\nDetails: {path}'
        print(message)
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror('VoiceLoom could not start', message, parent=root)
            root.destroy()
        except Exception:
            pass
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
