"""Exercise the actual installed runtime without external Python or model caches."""
import json
import subprocess
import threading
from pathlib import Path

def run(data, base):
    import tkinter as tk
    import numpy as np
    import soundfile as sf
    import sounddevice as sd
    from audio_engine import Engine
    from voice_catalog import BY_ID, SAMPLES
    from app import App
    results = {'runtime': 'private Python', 'offline_models': True}
    try:
        root = tk.Tk()
        root.withdraw()
        app = App(root, load_model=False, data_dir=data / 'test_studio')
        root.update()
        assert app.logo_image is not None
        app._close()
        results['ui'] = 'passed'
        results['audio_devices'] = len(sd.query_devices())
        engine = Engine()
        engine.load()
        settings = dict(speed=1., pause=.1, normalize=True, volume=90,
                        sample_rate=24000, channels='Mono', blend=None)
        voices = ['af_heart', 'bf_emma', 'ef_dora', 'ff_siwis', 'hf_alpha',
                  'if_sara', 'pf_dora', 'jf_alpha', 'zf_xiaobei']
        for voice_id in voices:
            voice = BY_ID[voice_id]
            result = engine.render(SAMPLES[voice['code']], voice, settings,
                                   data / 'test_audio', threading.Event(), lambda *args: None)
            audio, sr = sf.read(result['path'])
            assert sr == 24000 and len(audio) > 1000 and np.max(np.abs(audio)) > .001
            results[voice_id] = {'seconds': result['duration'], 'passed': True}
            (data / 'self-test.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        wav = Path(result['path'])
        ffmpeg = base / 'bin' / 'ffmpeg.exe'
        for ext in ('mp3', 'ogg'):
            target = wav.with_suffix('.' + ext)
            subprocess.run([str(ffmpeg), '-v', 'error', '-y', '-i', str(wav), str(target)],
                           check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            assert target.stat().st_size > 100
        results['exports'] = 'WAV, MP3, OGG passed'
        results['status'] = 'passed'
        return 0
    except Exception:
        import traceback
        results['status'] = 'failed'
        results['error'] = traceback.format_exc()
        print(results['error'])
        return 1
    finally:
        (data / 'self-test.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
