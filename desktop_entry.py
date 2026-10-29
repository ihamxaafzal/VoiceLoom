"""Installed application entry point; all state stays outside the installation."""
import os
from pathlib import Path
import sys
import traceback

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
DATA = Path(os.environ.get('VOICELOOM_DATA_DIR') or Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'VoiceLoom')
DATA.mkdir(parents=True, exist_ok=True)
os.environ['VOICELOOM_MODEL_DIR'] = str(BASE / 'models')
os.environ['HF_HOME'] = str(DATA / 'cache' / 'huggingface')
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['PATH'] = str(BASE / 'bin') + os.pathsep + os.environ.get('PATH', '')
os.environ['PYTHONPYCACHEPREFIX'] = str(DATA / 'cache' / 'pycache')
os.chdir(DATA)
log_dir = DATA / 'logs'
log_dir.mkdir(exist_ok=True)
log = (log_dir / 'startup.log').open('a', encoding='utf-8', buffering=1)
sys.stdout = sys.stderr = log

def main():
    if '--self-test' in sys.argv:
        from installed_self_test import run
        return run(DATA, BASE)
    import tkinter as tk
    from app import App
    root = tk.Tk()
    app = App(root, data_dir=DATA / 'studio_data', load_model='--ui-only' not in sys.argv)
    if '--smoke-ui' in sys.argv:
        root.after(1800, app._close)
    root.mainloop()
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        traceback.print_exc()
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, f'{exc}\n\nDetails: {log_dir / "startup.log"}', 'VoiceLoom could not start', 0x10)
        raise SystemExit(1)
