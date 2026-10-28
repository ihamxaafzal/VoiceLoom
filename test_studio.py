"""Focused regression checks for rendering and project/UI behavior."""
import tempfile
import asyncio
import threading
import time
import shutil
import unittest
from unittest.mock import patch
from pathlib import Path
import tkinter as tk
import numpy as np
import soundfile as sf
from app import App
from audio_engine import Engine, Cancelled, script_chunks
from voice_catalog import VOICES, BY_ID, LANGUAGES, ENGLISH_CODES


class FakePipeline:
    def __init__(self):
        self.calls = []

    def load_voice(self, voice):
        return np.ones((2, 3), dtype=np.float32) * (1 if voice == 'af_heart' else 3)

    def __call__(self, text, voice, speed):
        self.calls.append((text, voice, speed))
        yield text, '', np.sin(np.linspace(0, 15, 2400)).astype(np.float32)*.3


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = App(self.root, load_model=False, data_dir=self.temp.name)
        self.root.update()

    def tearDown(self):
        self.app._close()
        self.temp.cleanup()

    def test_catalog_filters_and_language_safe_blend(self):
        self.assertEqual(len(VOICES), 101)
        self.assertEqual(len(BY_ID), 101)
        self.assertEqual(sum(v['code'] in ENGLISH_CODES for v in VOICES), 75)
        self.assertEqual(set(v['code'] for v in VOICES), set(LANGUAGES))
        self.app.blend.set('af_bella')
        self.app._pick('hf_alpha')
        self.assertEqual(self.app.blend.get(), 'None')
        self.assertEqual(self.app.selected['code'], 'h')
        self.app.search.set('xiaobei')
        self.assertEqual(len(self.app.voice_frame.winfo_children()), 1)

    def test_online_filters_and_blend_safety(self):
        self.app.language.set('English (all accents)')
        self.assertEqual(len(self.app.voice_frame.winfo_children()), 75)
        self.app.source.set('Online · Edge English')
        self.assertEqual(len(self.app.voice_frame.winfo_children()), 47)
        self.app.blend.set('af_bella')
        self.app._pick('en-US-AriaNeural')
        self.assertEqual(self.app.blend.get(), 'None')
        self.assertEqual(str(self.app.blend_combo['state']), 'disabled')
        self.assertIn('Microsoft', self.app.active_sub.cget('text'))
        self.assertEqual(self.app.gen_btn['state'], 'normal')
        project = self.app._project()
        self.app._apply_project(project)
        project['settings']['blend'] = 'af_bella'
        with self.assertRaises(ValueError):
            self.app._apply_project(project)

    def test_online_network_wait_can_be_cancelled(self):
        class SlowSpeech:
            def __init__(self, *args, **kwargs):
                pass

            async def stream(self):
                await asyncio.sleep(30)
                yield {'type': 'audio', 'data': b''}

        cancel = threading.Event()
        timer = threading.Timer(.1, cancel.set)
        timer.start()
        started = time.monotonic()
        with patch('edge_tts.Communicate', SlowSpeech):
            with self.assertRaises(Cancelled):
                Engine().edge_parts('A sample.', BY_ID['en-US-AriaNeural'], self.app._settings(), cancel, lambda *a: None)
        timer.join()
        self.assertLess(time.monotonic()-started, 3)

    def test_project_roundtrip_and_validation(self):
        self.app._pick('bf_emma')
        self.app.speed.set(.8)
        self.app.blend.set('bf_lily')
        self.app.txt.delete('1.0', 'end')
        self.app.txt.insert('1.0', 'A saved story.')
        project = self.app._project()
        self.app._pick('af_heart')
        self.app._apply_project(project)
        self.assertEqual(self.app.selected['id'], 'bf_emma')
        self.assertEqual(self.app.blend.get(), 'bf_lily')
        self.assertEqual(self.app.speed.get(), .8)
        self.app._persist()
        self.assertTrue((Path(self.temp.name)/'session.json').exists())
        project['settings']['blend'] = 'hf_alpha'
        with self.assertRaises(ValueError):
            self.app._apply_project(project)

    def test_voice_reminders_persist_search_and_stay_per_voice(self):
        self.app._save_voice_note('bf_emma', 'History Shorts')
        self.app._save_voice_note('en-US-EmmaNeural', 'Travel Channel')
        self.app._pick('bf_emma')
        self.assertIn('History Shorts', self.app.active_sub.cget('text'))
        self.app.search.set('history shorts')
        self.assertEqual(len(self.app.voice_frame.winfo_children()), 1)
        self.app.voice_notes = {}
        self.app._restore_voice_notes()
        self.assertEqual(self.app.voice_notes['bf_emma'], 'History Shorts')
        self.assertEqual(self.app.voice_notes['en-US-EmmaNeural'], 'Travel Channel')
        self.app._apply_project(dict(voice='af_heart', text='A new project.', settings={}))
        self.assertEqual(self.app.voice_notes['bf_emma'], 'History Shorts')
        self.app._save_voice_note('bf_emma', '')
        self.app.voice_notes = {}
        self.app._restore_voice_notes()
        self.assertNotIn('bf_emma', self.app.voice_notes)
        self.assertEqual(self.app.voice_notes['en-US-EmmaNeural'], 'Travel Channel')

    def test_reminder_save_failure_and_invalid_length(self):
        self.app._save_voice_note('af_heart', 'Main Channel')
        with patch('app.atomic_json', side_effect=OSError('Disk unavailable')):
            with self.assertRaises(OSError):
                self.app._save_voice_note('af_heart', 'Unsaved change')
        self.assertEqual(self.app.voice_notes['af_heart'], 'Main Channel')
        with self.assertRaises(ValueError):
            self.app._save_voice_note('af_heart', 'x'*301)

    def test_render_resampling_stereo_mix_and_cancel(self):
        engine = Engine()
        pipe = FakePipeline()
        engine.pipelines['a'] = pipe
        settings = self.app._settings()
        settings.update(sample_rate=48000, channels='Stereo', blend='af_bella', blend_ratio=25)
        report = []
        result = engine.render('First passage.\nSecond passage.', BY_ID['af_heart'], settings,
                               self.temp.name, threading.Event(), lambda *a: report.append(a))
        audio, sr = sf.read(result['path'])
        self.assertEqual(sr, 48000)
        self.assertEqual(audio.shape[1], 2)
        self.assertTrue(np.max(np.abs(audio)) <= 1)
        self.assertAlmostEqual(float(pipe.calls[0][1][0, 0]), 1.5)
        self.assertEqual(report[-1][0], 1.)
        self.app._select_audio(result)
        self.root.update()
        self.assertIsNotNone(self.app.audio)
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(Cancelled):
            engine.render('Cancelled.', BY_ID['af_heart'], settings, self.temp.name, cancel, lambda *a: None)

    def test_unicode_chunks_keep_all_content(self):
        text = '这是一个很长的中文故事。'*100
        chunks = script_chunks(text)
        self.assertEqual(''.join(chunks), text)
        self.assertTrue(all(len(c) <= 160 for c in chunks))

    def test_controls_fit_minimum_window(self):
        self.app._save_voice_note('af_heart', 'My YouTube channel — history and documentary narration')
        self.root.deiconify()
        self.root.geometry('1100x820')
        self.root.update()
        for widget in [self.app.gen_btn, self.app.cancel_btn, self.app.progress]:
            self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),
                                 self.app.editor_tab.winfo_rooty()+self.app.editor_tab.winfo_height())
        for widget in self.app.export_buttons:
            self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),
                                 self.root.winfo_rooty()+self.root.winfo_height())
        self.assertLessEqual(self.app.branding.winfo_rootx()+self.app.branding.winfo_width(),
                             self.root.winfo_rootx()+self.root.winfo_width())

    def test_wav_flac_mp3_exports(self):
        engine = Engine()
        engine.pipelines['a'] = FakePipeline()
        result = engine.render('Export check.', BY_ID['af_heart'], self.app._settings(),
                               self.temp.name, threading.Event(), lambda *v: None)
        self.app._select_audio(result)
        formats = ['wav', 'flac'] + (['mp3'] if shutil.which('ffmpeg') else [])
        for fmt in formats:
            target = str(Path(self.temp.name) / ('export.'+fmt))
            with patch('app.filedialog.asksaveasfilename', return_value=target):
                self.app._export(fmt)
            deadline = time.monotonic() + 15
            while not Path(target).exists() and time.monotonic() < deadline:
                self.root.update()
                time.sleep(.05)
            self.assertTrue(Path(target).exists(), fmt)
            audio, sr = sf.read(target)
            self.assertEqual(sr, result['sample_rate'])
            self.assertGreater(len(audio), 0)


if __name__ == '__main__':
    unittest.main()
