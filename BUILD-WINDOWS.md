# VoiceLoom Windows installer

The release uses a private, isolated Python 3.12 x64 runtime. The small
VoiceLoom.exe launcher starts runtime/pythonw.exe with -I -B, so it does not
use the recipient's Python installation, PYTHONPATH or user site packages.
Python, Tcl/Tk, CPU PyTorch, all speech frontends and package resources travel
with the application. No pip or network installation runs on the user's PC.

## Build

Use a dedicated Python 3.12 x64 build environment with requirements.txt,
CPU torch, en_core_web_sm, espeakng-loader and PyInstaller installed. Install
setuptools below 81 as required by the project. The build script copies the
environment's site-packages: use a speech-only environment, and do not include
personal files, development credentials or unrelated packages in that folder.

Download the Kokoro-82M snapshot with config.json, kokoro-v1_0.pth and all
54 voices/*.pt. Use an FFmpeg Windows x64 executable with its license and
build/source notices. Install Inno Setup 6.7 or later.

```powershell
python build_release.py --stage ..\payload --models C:\path\to\Kokoro-snapshot --ffmpeg C:\path\to\ffmpeg.exe
Copy-Item INSTALL-NOTES.txt ..\payload\INSTALL-NOTES.txt
# Copy upstream model card, Apache 2.0 license and FFmpeg notices into
# ..\payload\ThirdPartyNotices before compiling.
& 'C:\path\to\ISCC.exe' /DPayloadDir="C:\path\to\payload" /DReleaseDir="C:\path\to\release" VoiceLoom.iss
```

The package metadata and upstream license files remain in runtime/Lib/site-packages.
Additional notices and an exact package inventory are in ThirdPartyNotices.
The model card is from https://huggingface.co/hexgrad/Kokoro-82M .

## Verification

Set VOICELOOM_DATA_DIR to an empty writable test directory, remove Python
and FFmpeg from PATH, and run the bundled executable with --self-test.
It checks Tk branding, the audio backend, real offline rendering in all
nine language groups, and MP3/OGG conversion. Results are in self-test.json.
Use --ui-only --smoke-ui for an automatically closing UI smoke test.

The 2026-10-29 build passed the isolated runtime synthesis and export checks.
Online voices still require the upstream service and an internet connection.
This build has not been tested in a separate clean Windows VM.

Installed state lives in %LOCALAPPDATA%\VoiceLoom. Upgrades and uninstall
preserve that directory. The original project's existing sessions are not
included in the installer. The release is unsigned.
