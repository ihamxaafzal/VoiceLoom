# Changelog

## 1.0.0 — 2026-10-29

### Windows installer

- Added a standalone Windows 10/11 x64 installer distributed as a release ZIP.
- Bundled private Python 3.12, CPU PyTorch, speech dependencies, Kokoro-82M, all 54 local voices, pronunciation resources, and FFmpeg.
- Enabled local narration without package installation or model downloads on the recipient's computer.
- Added per-user installation, Start menu integration, an optional desktop shortcut, and uninstall support.
- Kept installed settings, recordings, and logs in `%LOCALAPPDATA%\VoiceLoom`, preserved during upgrades and uninstall.
- Added packaging source, offline smoke checks, third-party notices, a package inventory, and release checksums.

### Documentation

- Added a prominent installer download link and clear ZIP extraction instructions.
- Documented installer requirements, local versus online voice behavior, saved data, updates, and uninstall.
- Retained a separate source installation path for developers.

### Verification

- Passed real offline synthesis across all nine language groups and WAV/MP3/OGG conversion.
- Passed native EXE launch, installed EXE launch, installation, and uninstall checks.
- Confirmed saved state remains after uninstall.
- Passed three startup regression checks. A separate clean Windows VM and live online synthesis were not tested.
