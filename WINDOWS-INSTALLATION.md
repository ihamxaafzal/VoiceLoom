# Windows installation

## Download and install

1. Open the [latest VoiceLoom release](https://github.com/ihamxaafzal/VoiceLoom/releases/latest).
2. Under **Assets**, download **VoiceLoom-Setup-1.0.0-Windows-x64.zip**.
3. Right-click the ZIP and select **Extract All**.
4. Run **VoiceLoom-Setup-1.0.0-Windows-x64.exe**.
5. Complete the wizard, optionally enable a desktop shortcut, and open VoiceLoom from the Start menu.

You do not need to install Python, pip, speech libraries, eSpeak NG, or FFmpeg separately. The setup contains a private Python 3.12 runtime, CPU PyTorch, Kokoro-82M, all 54 local voices, language resources, and FFmpeg.

**Supported system:** Windows 10/11, 64-bit. At least 8 GB RAM and 4 GB free disk space are recommended; allow additional space for recordings and keeping the downloaded ZIP and extracted setup.

The ZIP is approximately 760 MiB because it includes the local AI model. Bundled local voices work offline after installation. Online Edge voices always require internet and send the selected script to the speech service. The first model load may take a little time.

## Which download should I choose?

| Download | Intended use |
| --- | --- |
| `VoiceLoom-Setup-1.0.0-Windows-x64.zip` | Normal Windows installation; extract it and run the setup EXE |
| `VoiceLoom-BuildKit.zip` | Packaging source and rebuild instructions for developers |
| `VoiceLoom-Read-Me.txt` | Installation notes and verification details |
| `SHA256SUMS.txt` | Integrity checksums for release files |
| GitHub's `Source code (zip)` / `Source code (tar.gz)` | Repository source; does not include the installer or bundled runtime |

## Verify the download

Download `SHA256SUMS.txt` from the same release and compare the ZIP's SHA-256 value:

```powershell
Get-FileHash .\VoiceLoom-Setup-1.0.0-Windows-x64.zip -Algorithm SHA256
```

The installer is unsigned, so Windows may display a publisher or SmartScreen warning. A matching checksum confirms integrity against the release checksum; it is not a digital signature.

## Files and user data

- Default app location: `%LOCALAPPDATA%\Programs\VoiceLoom`.
- Settings, recordings, and logs: `%LOCALAPPDATA%\VoiceLoom`.
- Startup log: `%LOCALAPPDATA%\VoiceLoom\logs\startup.log`.
- Project files remain in the locations you selected when saving them.

Installation is per user and does not require administrator privileges. VoiceLoom uses its own runtime rather than a system Python installation. Existing sessions from source-based copies are not automatically imported; open your saved JSON project from the app.

## Update or uninstall

Close VoiceLoom, download the newer setup from Releases, and run it. Use the same installation directory when updating. To uninstall, open **Windows Settings > Apps > VoiceLoom > Uninstall**. Updates and uninstall preserve the user data folder and saved projects.

## Verified for version 1.0.0

The bundled runtime passed real offline rendering in American/British English, Spanish, French, Hindi, Italian, Portuguese, Japanese, and Mandarin Chinese. Interface/branding, the audio backend, WAV/MP3/OGG output, installed EXE startup, installation, and uninstall were checked. Saved state was preserved after uninstall. A separate clean Windows VM and live online synthesis were not tested.
