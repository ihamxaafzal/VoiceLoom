"""Small native entry point that uses only the bundled private Python runtime."""
import ctypes
from pathlib import Path
import subprocess
import sys

def main():
    base = Path(sys.executable).resolve().parent
    python = base / 'runtime' / 'pythonw.exe'
    script = base / 'app' / 'desktop_entry.py'
    try:
        if not python.is_file() or not script.is_file():
            raise RuntimeError('Application files are missing. Please reinstall VoiceLoom.')
        child = subprocess.Popen([str(python), '-I', '-B', str(script), *sys.argv[1:]],
                                 cwd=str(base), creationflags=subprocess.CREATE_NO_WINDOW)
        return child.wait()
    except Exception as exc:
        ctypes.windll.user32.MessageBoxW(None, str(exc), 'VoiceLoom', 0x10)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
