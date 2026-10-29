# Third-party notices

## Scope of the VoiceLoom license

Original VoiceLoom application code and documentation are licensed under **Apache-2.0**; see [LICENSE](LICENSE) and [NOTICE](NOTICE). This grant applies to original contributions that their authors have the right to license. It does not relicense bundled libraries, native binaries, model weights, voice assets, dictionaries, or online services.

The Windows distribution contains components under several licenses, including GPL and LGPL. Their applicable conditions remain in force. The Apache-2.0 grant does not restrict rights granted by those licenses; where a combined work is subject to GPLv3, the applicable GPLv3 distribution requirements must also be satisfied. The entire installer must not be described as exclusively Apache-2.0 licensed.

## Principal components in the Windows 1.0.0 build

| Component | Version / identification | License and upstream |
| --- | --- | --- |
| Python | 3.12.0, Windows x64 | PSF license and bundled notices; [Python licensing](https://docs.python.org/3/license.html) |
| Kokoro Python package | 0.9.4 | Apache-2.0; [hexgrad/kokoro](https://github.com/hexgrad/kokoro) |
| Kokoro model and 54 local voice files | Kokoro-82M v1.0; snapshot `f3ff3571791e39611d31c381e3a41a3af07b4987` | Apache-2.0 as declared by the [model card](https://huggingface.co/hexgrad/Kokoro-82M); retain the upstream card and attribution |
| Misaki | 0.9.4 | Apache-2.0; [hexgrad/misaki](https://github.com/hexgrad/misaki) |
| PyTorch | 2.12.0, CPU runtime | BSD-style license and additional upstream notices; [pytorch/pytorch](https://github.com/pytorch/pytorch) |
| edge-tts | 7.3.1 | LGPLv3, with `srt_composer.py` under MIT; [exact source release](https://pypi.org/project/edge-tts/7.3.1/#files) |
| phonemizer-fork | 3.3.2 | GPLv3; [exact source release](https://pypi.org/project/phonemizer-fork/3.3.2/#files) |
| eSpeak NG native library and pronunciation data | eSpeak NG 1.52.0, shipped through espeakng-loader 0.2.4 | eSpeak NG is GPLv3-or-later; the wrapper has its own terms. See [eSpeak NG](https://github.com/espeak-ng/espeak-ng) and [loader project](https://github.com/thewh1teagle/espeakng-loader). A wrapper license does not replace the native library's license. |
| FFmpeg | `8.1.1-full_build-www.gyan.dev` | GPLv3 build; see [FFMPEG-SOURCE.md](FFMPEG-SOURCE.md), its original LICENSE, and build inventory |
| English spaCy model | en_core_web_sm 3.8.0 | MIT and the model's `LICENSES_SOURCES`; [spaCy English models](https://spacy.io/models/en) |
| Audio, numerical, and language dependencies | See packaged inventory | Each package retains its own license; authoritative license files are distributed with the packages |

The package inventory is a record of installed package metadata, not a legal classification or complete transitive native-library audit. A missing or `UNKNOWN` metadata license is not permission to relicense that component. Consult its actual license files and upstream source.

## Model and voice attribution

VoiceLoom uses Kokoro through its published model and voice assets; it does not claim to have created those voices or model weights. The upstream Kokoro model card credits its authors and training sources, including Koniwa and SIWIS. Those credits are preserved in the distributed model card. See the [upstream attribution section](https://huggingface.co/hexgrad/Kokoro-82M#creative-commons-attribution).

Apache-2.0 permits redistribution subject to its conditions, including retaining the license and applicable attribution/NOTICE text and marking modifications to upstream files. It is not a trademark endorsement or a general grant of rights over third-party identities or every possible generated output.

## Online voices and service terms

Online voices are accessed through Microsoft's online speech service using edge-tts. No Microsoft voice model is bundled. The edge-tts software license does not grant ownership of Microsoft voices or override the provider's service terms. No affiliation, sponsorship, or endorsement by Microsoft is claimed. This release does not establish a blanket permission for commercial use of the online service or its outputs.

## Source access and modification

- VoiceLoom application and packaging source: [repository](https://github.com/ihamxaafzal/VoiceLoom) and the release's `VoiceLoom-BuildKit.zip`.
- Installed Python dependency sources and their package license files remain in `runtime/Lib/site-packages`; the runtime loads those files directly rather than encrypting them.
- Versioned source distributions for edge-tts 7.3.1 and phonemizer-fork 3.3.2 are linked above and supplied in the companion licensing archive.
- eSpeak NG reports version 1.52.0 through its native API; [upstream source tag](https://github.com/espeak-ng/espeak-ng/tree/1.52.0). The wrapper wheel does not supply a complete native build recipe, so exact native build provenance has not been independently verified.
- FFmpeg source revision, build configuration, external-library inventory, and source-access limitations are documented in [FFMPEG-SOURCE.md](FFMPEG-SOURCE.md).
- Users' rights to modify, replace, or debug third-party components under their licenses are not restricted by VoiceLoom's license notice.

## Files accompanying the release

The companion **VoiceLoom-1.0.0-Licenses.zip** contains the project license, NOTICE, this document, FFmpeg source details and original build notices, the Kokoro model card, the package inventory, and copies of license/NOTICE files from the shipped runtime. The installer itself also retains upstream package license files and its `ThirdPartyNotices` directory.

These notices document the components and their respective terms. They are not a certification that every third-party redistribution obligation has been independently audited; in particular, see the corresponding-source limitation for the prebuilt FFmpeg full build.
