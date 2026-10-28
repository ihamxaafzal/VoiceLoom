"""Lazy model loading and audio processing; independent of Tk widgets."""
import math
import asyncio
import io
import re
import threading
import time
import uuid
from pathlib import Path


class Cancelled(Exception):
    pass


def script_chunks(text, limit=160):
    # Conservative Unicode character limit also protects non-English G2P
    # pipelines, which otherwise truncate long phoneme sequences.
    chunks = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        while paragraph:
            end = min(limit, len(paragraph))
            if end < len(paragraph):
                matches = list(re.finditer(r'[.!?。！？,，;；\s]', paragraph[:end]))
                if matches and matches[-1].end() >= limit // 2:
                    end = matches[-1].end()
            chunks.append(paragraph[:end].strip())
            paragraph = paragraph[end:].strip()
    return [c for c in chunks if c]


class Engine:
    def __init__(self):
        self.pipelines = {}
        self.device = 'cpu'
        self.device_label = 'CPU'

    def load(self):
        import torch
        from kokoro import KPipeline
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device_label = torch.cuda.get_device_name(0) if self.device == 'cuda' else 'CPU'
        try:
            self.pipelines['a'] = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M', device=self.device)
        except RuntimeError:
            if self.device != 'cuda':
                raise
            self.device = 'cpu'
            self.device_label = 'CPU (GPU unavailable)'
            self.pipelines['a'] = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M', device='cpu')

    def pipeline(self, code):
        if code not in self.pipelines:
            from kokoro import KPipeline
            self.pipelines[code] = KPipeline(lang_code=code, repo_id='hexgrad/Kokoro-82M', model=self.pipelines['a'].model)
        return self.pipelines[code]

    def edge_parts(self, text, voice, settings, cancel, progress):
        """Fetch online audio with cancellation even while awaiting the network."""
        import edge_tts
        import numpy as np
        import soundfile as sf
        if settings.get('blend'):
            raise ValueError('Voice blending is available for local Kokoro voices only.')
        chunks = script_chunks(text, limit=1800)

        async def fetch():
            parts = []
            for i, chunk in enumerate(chunks):
                if cancel.is_set():
                    raise Cancelled()
                data = bytearray()
                rate = f"{round((settings['speed']-1)*100):+d}%"
                speech = edge_tts.Communicate(chunk, voice=voice['id'], rate=rate,
                                              connect_timeout=10, receive_timeout=20)
                async for event in speech.stream():
                    if cancel.is_set():
                        raise Cancelled()
                    if event['type'] == 'audio':
                        data.extend(event['data'])
                if not data:
                    raise RuntimeError('The online voice service returned no audio.')
                audio, sr = sf.read(io.BytesIO(data), dtype='float32')
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                if sr != 24000:
                    from scipy.signal import resample_poly
                    g = math.gcd(sr, 24000)
                    audio = resample_poly(audio, 24000//g, sr//g).astype(np.float32)
                parts.append(audio)
                if i < len(chunks)-1 and settings['pause']:
                    parts.append(np.zeros(int(24000*settings['pause']), dtype=np.float32))
                progress((i+1)/len(chunks), f'Online English voice · passage {i+1} of {len(chunks)}')
            return parts

        async def run():
            task = asyncio.create_task(fetch())
            try:
                while not task.done():
                    await asyncio.wait({task}, timeout=.15)
                    if cancel.is_set():
                        task.cancel()
                        await asyncio.gather(task, return_exceptions=True)
                        raise Cancelled()
                return await task
            finally:
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
        return asyncio.run(run())

    def render(self, text, voice, settings, folder, cancel, progress):
        import numpy as np
        import soundfile as sf
        from scipy.signal import resample_poly
        started = time.perf_counter()
        online = voice.get('engine') == 'edge'
        if online:
            parts = self.edge_parts(text, voice, settings, cancel, progress)
        else:
            parts = self.kokoro_parts(text, voice, settings, cancel, progress)
        if not parts:
            raise RuntimeError('No audio produced. Check the script language and voice.')
        audio = np.concatenate(parts)
        peak = float(np.max(np.abs(audio)))
        if settings['normalize'] and peak > 0:
            audio = audio * (0.95 / peak)
        audio = np.clip(audio * settings['volume']/100, -1, 1)
        sr = settings['sample_rate']
        if sr != 24000:
            divisor = math.gcd(sr, 24000)
            audio = resample_poly(audio, sr//divisor, 24000//divisor).astype(np.float32)
        if settings['channels'] == 'Stereo':
            audio = np.column_stack((audio, audio))
        if cancel.is_set():
            raise Cancelled()
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{time.strftime('%Y%m%d_%H%M%S')}_{voice['id']}_{uuid.uuid4().hex[:6]}.wav"
        sf.write(str(path), audio, sr, subtype='PCM_16')
        return dict(path=str(path), voice=voice['name'], voice_id=voice['id'],
                    engine=voice.get('engine', 'kokoro'),
                    language=voice['language'], duration=len(audio)/sr, sample_rate=sr,
                    channels=settings['channels'], elapsed=time.perf_counter()-started,
                    created=time.strftime('%H:%M'), text=text, settings=settings)

    def kokoro_parts(self, text, voice, settings, cancel, progress):
        import numpy as np
        pipe = self.pipeline(voice['code'])
        chunks = script_chunks(text)
        parts = []
        blend = settings.get('blend')
        voice_arg = voice['id']
        if blend:
            weight = settings['blend_ratio'] / 100
            voice_arg = pipe.load_voice(voice['id']) * (1-weight) + pipe.load_voice(blend) * weight
        for i, chunk in enumerate(chunks):
            if cancel.is_set():
                raise Cancelled()
            for _, _, audio in pipe(chunk, voice=voice_arg, speed=settings['speed']):
                if cancel.is_set():
                    raise Cancelled()
                if audio is not None:
                    if hasattr(audio, 'detach'):
                        audio = audio.detach().cpu().numpy()
                    parts.append(np.asarray(audio, dtype=np.float32))
            if i < len(chunks)-1 and settings['pause']:
                parts.append(np.zeros(int(24000 * settings['pause']), dtype=np.float32))
            progress((i+1)/len(chunks), f'Rendering passage {i+1} of {len(chunks)}')
        if not parts:
            raise RuntimeError('No audio produced. Check the script language and voice.')
        return parts
