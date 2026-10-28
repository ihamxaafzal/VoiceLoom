<p align="center">

  <img src="assets/voice-narrator-logo.png" alt="VoiceLoom logo" width="120">

</p>



# VoiceLoom



A Windows desktop workspace for turning scripts into narration with local Kokoro voices and online Microsoft Edge voices. Browse voices, adjust delivery, preview audio, and export finished narration from one interface.



**Made with love by [Hamza](https://github.com/ihamxaafzal).**



## Preview

![VoiceLoom demo: voice selection, narration generation, and waveform playback](assets/voiceloom-demo.gif)

Browse the voice library, compose a script, generate local narration, and review the waveform before exporting.

## Features



- 101 voices in the bundled catalog: 54 local Kokoro voices and 47 online English voices.

- 75 English voices, with American, British, and additional regional accents.

- Local support for English, Spanish, French, Hindi, Italian, Japanese, Brazilian Portuguese, and Mandarin Chinese.

- Searchable voice library, favorites, and private channel/reminder labels.

- Speed, volume, passage pauses, normalization, output sample rate, and mono/stereo controls.

- Compatible local voice blending and delivery presets.

- Script import, word counts, waveform display, playback, and click-to-seek.

- WAV and FLAC export; MP3 export with FFmpeg installed.

- JSON projects, session restore, and recent render history.

- CPU operation with automatic CUDA detection when a compatible PyTorch build is installed.



## Requirements



| Component | Requirement |

| --- | --- |

| Operating system | 64-bit Windows; the included launch and setup scripts target Windows |

| Python | 3.10-3.12, 64-bit; Python 3.12 recommended |

| Python installer options | pip, venv, and Tcl/Tk (Tkinter) |

| Storage | Several GB of free space for dependencies and downloaded model assets |

| Internet | Required for installation and first model download; always required for online voices |

| GPU | Optional; the default setup installs CPU PyTorch |

| eSpeak NG | Required for local Hindi, French, Spanish, Italian, and Portuguese phonemization; optional English fallback |

| FFmpeg | Optional; required for MP3 export |



Python 3.13 and newer are not supported by the bundled setup/launcher checks. Tkinter comes with the official Windows Python installer; do not install it with pip.



## Quick start on Windows



1. Install [Python 3.12 for Windows](https://www.python.org/downloads/windows/), selecting the 64-bit installer with pip and Tcl/Tk.

2. Download this repository using **Code > Download ZIP**, then **Extract All**, or clone it:



   ```powershell

   git clone https://github.com/ihamxaafzal/VoiceLoom.git

   cd VoiceLoom

   ```



3. Run **setup.bat** from the extracted project folder:



   ```powershell

   .\setup.bat

   ```



   Setup creates a local `.venv`, installs CPU PyTorch and the packages in `requirements.txt`, and checks the application dependencies. Keep the terminal open until it reports **Setup complete**.



4. Start the application:



   ```powershell

   .\start.bat

   ```



The first local render downloads Kokoro model/voice assets from Hugging Face. Later local renders can use cached assets. Run setup on each computer; virtual environments should not be copied between PCs. Keep the `assets` folder beside `app.py`.



### Manual installation



Run these commands in PowerShell from the project folder. Activation is optional because each command uses the virtual environment's Python directly.



```powershell

py -3.12 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip

.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe launcher.py --check

.\.venv\Scripts\python.exe launcher.py

```



### Python libraries



`requirements.txt` defines the supported package ranges. PyTorch is installed separately by `setup.bat`.



| Library | Purpose |

| --- | --- |

| `torch` | Local model inference on CPU or supported GPU |

| `kokoro` | Local text-to-speech pipeline |

| `misaki[en,zh]` | English and Mandarin text processing |

| `pyopenjtalk-plus`, `fugashi`, `jaconv`, `mojimoji`, `unidic-lite` | Japanese language frontend |

| `numpy`, `scipy` | Audio arrays, mixing, and resampling |

| `soundfile` | Audio reading and WAV/FLAC writing |

| `sounddevice` | Desktop audio playback |

| `edge-tts` | Microsoft Edge online speech |

| `setuptools` | Compatibility support for language dependencies |

| `tkinter` | Desktop interface; included with Python, not installed through pip |



### Language setup: eSpeak NG



Install the 64-bit Windows MSI from the official [eSpeak NG releases](https://github.com/espeak-ng/espeak-ng/releases). Restart VoiceLoom after installation.



If the phonemizer cannot locate the DLL, point it to the installed library before starting the app:



```powershell

$env:PHONEMIZER_ESPEAK_LIBRARY = 'C:\Program Files\eSpeak NG\libespeak-ng.dll'

.\start.bat

```



Adjust the path if eSpeak NG is installed elsewhere. See the [Phonemizer installation guide](https://bootphon.github.io/phonemizer/install.html) for backend setup.



Japanese and Mandarin frontend packages are included in `requirements.txt`. Use text in the selected voice's language. Kokoro has no native Urdu voice; Hindi voices expect Hindi text rather than Urdu or Roman Urdu.



### Optional: MP3 export



Install FFmpeg using the options linked from the [official download page](https://ffmpeg.org/download.html), add its `bin` directory to `PATH`, and reopen the app. Verify it is available:



```powershell

ffmpeg -version

```



WAV and FLAC export do not require FFmpeg.



### Optional: NVIDIA GPU acceleration



The default installation works without a GPU. For CUDA, install a compatible NVIDIA driver and use the command generated by the official [PyTorch installer selector](https://pytorch.org/get-started/locally/) for Windows, pip, and your supported CUDA version. Run that command using `.\.venv\Scripts\python.exe -m pip` in this project's environment. VoiceLoom detects CUDA during engine loading and can fall back to CPU.



## Usage



1. Choose a voice and write or import a script in its language.

2. Use **Preview** to hear the voice's sample sentence.

3. Adjust speed, volume, passage pauses, output settings, or a preset.

4. Select **Generate narration** and review the waveform/playback.

5. Export WAV, FLAC, or MP3, or save the project to continue later.



Use **Explore 47 new English voices** to browse online voices. Voice blending is available only for compatible local Kokoro voices. Presets adjust speed and pauses; they do not control model emotion. Cancellation takes effect between local model segments, after the current inference call finishes.



| Shortcut | Action |

| --- | --- |

| Ctrl+Enter | Generate narration |

| Ctrl+S | Save project |

| Ctrl+O | Open project |



## Data and network behavior



- Local Kokoro synthesis runs on the computer after required assets are downloaded.

- Online voices send the selected script to Microsoft's speech service and require an internet connection. Availability depends on that service.

- The bundled Edge voice catalog is a snapshot; VoiceLoom does not refresh it automatically.

- `studio_data/session.json` stores the last script, settings, favorites, and recent history.

- `studio_data/voice_notes.json` stores private channel/reminder labels; these labels are not included in speech requests.

- `studio_data/renders/` holds generated audio and previews. History lists the latest 50 renders; older audio remains on disk.

- Projects are saved as JSON to a location selected by the user. Stereo output duplicates the mono source; output sample-rate changes resample the audio.

- `.gitignore` excludes local sessions, rendered audio, logs, backups, environments, and model files.



## Troubleshooting



| Problem | Resolution |

| --- | --- |

| Python not found or unsupported | Install Python 3.12 64-bit with pip and Tcl/Tk, then rerun setup |

| Missing libraries or copied environment | Run `setup.bat` on the current computer |

| Setup failure | Read `logs/setup.log`; check internet access and available disk space |

| App closes during startup | Run `diagnose.bat`; inspect `logs/diagnostic.log` and `logs/startup.log` |

| Cannot write project logs | Launcher uses `%LOCALAPPDATA%/VoiceLoom/logs` as a fallback |

| Language backend missing | Install eSpeak NG or verify the language frontend packages |

| Online voice fails | Check the connection and service availability, or select a local voice |

| MP3 export unavailable | Install FFmpeg, add it to PATH, then reopen the app |

| No playback | Check the selected Windows output device and that audio playback is available |



For a folder/Python check without installing packages:



```powershell

.\setup.bat --check-paths

```



To check dependencies or open the interface without loading speech models:



```powershell

.\.venv\Scripts\python.exe launcher.py --check

.\.venv\Scripts\python.exe app.py --ui-only

```



## Development



```powershell

.\.venv\Scripts\python.exe -m unittest test_launcher test_studio -v

```



The regression suite uses a synthetic local pipeline and mocks online requests; it checks project handling, voice filtering, audio processing, cancellation, layout, and exports. The MP3 export check runs only when FFmpeg is available.



| File | Role |

| --- | --- |

| `app.py` | Tkinter workspace and project/session management |

| `audio_engine.py` | Synthesis, processing, playback preparation, and export |

| `voice_catalog.py`, `english_voices.json` | Voice metadata and language routing |

| `launcher.py` | Startup checks and diagnostics |

| `setup_project.py` | Virtual environment and dependency installation |

| `assets/` | Logo and window icon |



## Acknowledgments



VoiceLoom uses [Kokoro](https://github.com/hexgrad/kokoro), the [Kokoro-82M model](https://huggingface.co/hexgrad/Kokoro-82M), [Misaki](https://github.com/hexgrad/misaki), [edge-tts](https://github.com/rany2/edge-tts), and the libraries listed above. These components and model assets remain subject to their respective licenses and service terms.



## Contact



For questions or feedback, visit [Hamza's GitHub profile](https://github.com/ihamxaafzal) or [open an issue](https://github.com/ihamxaafzal/VoiceLoom/issues).

