"""Install using pathlib/subprocess argument lists, including paths with spaces."""
from datetime import datetime
import os
from pathlib import Path
import struct
import subprocess
import sys
import traceback

BASE = Path(__file__).resolve().parent


def check_paths(base):
    if not (3, 10) <= sys.version_info < (3, 13) or struct.calcsize('P') != 8:
        raise RuntimeError('Install Python 3.12 64-bit with pip and Tcl/Tk first.')
    for name in ('requirements.txt', 'launcher.py', 'app.py', 'english_voices.json'):
        if not (base/name).is_file():
            raise RuntimeError(f'Missing project file: {name}. Extract the complete ZIP before running setup.bat.')
    import tkinter  # Verify Tcl/Tk was included in the base Python installation.
    (base/'logs').mkdir(parents=True, exist_ok=True)
    temp = base/'studio_data'/'setup_tmp'
    temp.mkdir(parents=True, exist_ok=True)
    return temp


def run_step(label, args, base, env, log):
    print('\n'+label, flush=True)
    log.write('\nSTEP: '+label+'\nCOMMAND: '+repr(args)+'\n')
    log.flush()
    try:
        process = subprocess.Popen(args, cwd=str(base), env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except OSError as exc:
        raise RuntimeError(f'{label}: Windows could not start {args[0]!r}. {exc}') from exc
    for line in process.stdout:
        print(line, end='', flush=True)
        log.write(line)
        log.flush()
    code = process.wait()
    if code:
        raise RuntimeError(f'{label} failed with exit code {code}. See logs/setup.log for the exact error.')


def main():
    log = None
    stage = 'Checking project folder'
    try:
        (BASE/'logs').mkdir(parents=True, exist_ok=True)
        log = (BASE/'logs'/'setup.log').open('a', encoding='utf-8', buffering=1)
        print('Project folder:', BASE, flush=True)
        print('Base Python:', sys.executable, flush=True)
        log.write(f'\n=== {datetime.now().isoformat(timespec="seconds")} ===\nProject: {BASE}\nPython: {sys.executable}\n')
        temp = check_paths(BASE)
        if '--check-paths' in sys.argv:
            print('Path checks passed. No packages were installed.', flush=True)
            return 0
        env = dict(os.environ, TEMP=str(temp), TMP=str(temp), PYTHONIOENCODING='utf-8',
                   PYTHONUTF8='1', PIP_DISABLE_PIP_VERSION_CHECK='1')
        venv = BASE/'.venv'
        stage = 'Creating this laptop\'s Python environment'
        run_step(stage, [sys.executable, '-m', 'venv', str(venv)], BASE, env, log)
        python = venv/'Scripts'/'python.exe'
        if not python.is_file():
            raise RuntimeError(f'Python environment was not created at {python}. Review the step above.')
        steps = [
            ('Checking environment executable', [str(python), '-c', 'import sys; print(sys.executable)']),
            ('Updating pip', [str(python), '-m', 'pip', 'install', '--upgrade', 'pip']),
            ('Installing CPU PyTorch (large download)', [str(python), '-m', 'pip', 'install', 'torch', '--index-url', 'https://download.pytorch.org/whl/cpu']),
            ('Installing speech packages', [str(python), '-m', 'pip', 'install', '-r', str(BASE/'requirements.txt')]),
            ('Checking app dependencies', [str(python), str(BASE/'launcher.py'), '--check']),
        ]
        for stage, args in steps:
            run_step(stage, args, BASE, env, log)
        print('\nSetup complete. Run start.bat.', flush=True)
        print('No NVIDIA GPU is required. First local use downloads model assets.', flush=True)
        return 0
    except Exception as exc:
        print(f'\nSETUP FAILED AT: {stage}\n{exc}', flush=True)
        if log:
            log.write(f'FAILED AT: {stage}\n'+traceback.format_exc()+'\n')
            print('Details:', BASE/'logs'/'setup.log', flush=True)
        else:
            print('Extract the ZIP to a writable folder such as Documents and try again.', flush=True)
        return 1
    finally:
        if log:
            log.close()


if __name__ == '__main__':
    raise SystemExit(main())
