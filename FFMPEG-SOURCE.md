# FFmpeg source access — Windows release 1.0.0

## Exact bundled binary

VoiceLoom 1.0.0 distributes an unmodified, separate `ffmpeg.exe` executable from Gyan Doshi's Windows build:

- Version: **8.1.1-full_build-www.gyan.dev**.
- Build license: **GNU GPL version 3**, as stated in the original build README.
- Provider: [Gyan's FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/).
- Provider's release page: [8.1.1](https://github.com/GyanD/codexffmpeg/releases/tag/8.1.1).
- FFmpeg source commit recorded by the provider: **239f2c733de417201d7ad3b3b8b0d9b63285b2b1**.
- [Browse the exact FFmpeg core source](https://github.com/FFmpeg/FFmpeg/tree/239f2c733de417201d7ad3b3b8b0d9b63285b2b1).
- [Download the exact FFmpeg core source ZIP](https://github.com/ihamxaafzal/VoiceLoom/releases/download/v1.0.0/FFmpeg-239f2c733d-core-source.zip).
- [Upstream source archive](https://github.com/FFmpeg/FFmpeg/archive/239f2c733de417201d7ad3b3b8b0d9b63285b2b1.zip).

VoiceLoom invokes FFmpeg as a separate process for audio conversion. It does not modify the supplied FFmpeg executable or claim ownership of it.

## Build information and notices

The release's **VoiceLoom-1.0.0-Licenses.zip** includes:

- `ffmpeg/FFmpeg-LICENSE`: original GPLv3 license text.
- `ffmpeg/FFmpeg-README.txt`: the provider's original build information and external-library version inventory.
- `ffmpeg/ffmpeg-buildconf.txt`: the output of this exact binary's `-buildconf` command.
- `ffmpeg/ffmpeg-version.txt`: the exact binary's version output.
- `SOURCE-SHA256SUMS.txt`: integrity hashes for the core source archive and supplied Python source distributions.

The exact executable hash is recorded in `ffmpeg/ffmpeg-binary.sha256`. The installer places the executable at `app/bin/ffmpeg.exe`.

## Important source-coverage limitation

**The core source ZIP is not a complete corresponding-source bundle for the static full build.** This FFmpeg build statically incorporates external libraries listed in the original README. Corresponding-source requirements can also include those libraries, patches, and scripts needed to reproduce the distributed build. Their complete exact sources and build scripts have not been independently reconstructed or verified here.

The provider's source-commit link and library inventory are preserved to identify the binary accurately. These links and the core archive must not be presented as proof that all GPL source obligations for the full static binary have been fulfilled. A distributor must ensure the necessary corresponding source remains available, including the required linked components; see [GPLv3 section 6](https://github.com/FFmpeg/FFmpeg/blob/239f2c733de417201d7ad3b3b8b0d9b63285b2b1/COPYING.GPLv3#L217).

No open-ended written source-code offer or promise of a complete source bundle is made by this document. For licensing questions about this exact binary, use the [build provider's support repository](https://github.com/GyanD/codexffmpeg); report VoiceLoom packaging questions through [VoiceLoom issues](https://github.com/ihamxaafzal/VoiceLoom/issues).
