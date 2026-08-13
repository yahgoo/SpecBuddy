# Kokoro + HyperFrames Voiceover Reference

Use this reference when adding natural voiceover to a SpecBuddy HyperFrames demo.

## Environment Checks

Check for a repo-local TTS virtual environment and Kokoro support:

```bash
test -x .tts-venv/bin/python
.tts-venv/bin/python -c "import kokoro_onnx, soundfile; print('tts ok')"
which espeak-ng
```

If `.tts-venv` does not exist, create it and install the lightweight Kokoro path recommended by HyperFrames doctor:

```bash
python3 -m venv .tts-venv
.tts-venv/bin/python -m pip install --upgrade pip
.tts-venv/bin/python -m pip install kokoro-onnx soundfile
```

On macOS, Kokoro phonemization may need Homebrew eSpeak:

```bash
brew install espeak-ng
```

When invoking HyperFrames TTS, expose the Homebrew eSpeak library and data path:

```bash
HYPERFRAMES_PYTHON="$(pwd)/.tts-venv/bin/python" \
PHONEMIZER_ESPEAK_LIBRARY="/opt/homebrew/lib/libespeak-ng.dylib" \
ESPEAK_DATA_PATH="/opt/homebrew/share/espeak-ng-data" \
npx --yes hyperframes@0.7.107 tts --voice af_heart --speed 0.95 \
  -o /tmp/test-voice.wav /tmp/test-voice.txt
```

Verify that a test WAV has real duration and size:

```bash
ffprobe -v error -show_entries format=duration,size \
  -of default=noprint_wrappers=1 /tmp/test-voice.wav
```

## Per-Scene Synthesis

Write one file per scene:

```bash
printf '%s\n' 'SpecBuddy helps teams catch weak requirements before a coding agent starts building.' > /tmp/vo1.txt
```

Generate one WAV per scene:

```bash
mkdir -p output/demo-artifacts/specbuddy-video/assets/voice

HYPERFRAMES_PYTHON="$(pwd)/.tts-venv/bin/python" \
PHONEMIZER_ESPEAK_LIBRARY="/opt/homebrew/lib/libespeak-ng.dylib" \
ESPEAK_DATA_PATH="/opt/homebrew/share/espeak-ng-data" \
npx --yes hyperframes@0.7.107 tts --voice af_heart --speed 0.95 \
  -o output/demo-artifacts/specbuddy-video/assets/voice/scene-01.wav /tmp/vo1.txt
```

If the composition loads media relative to its own folder, copy or generate the same files into the composition asset folder:

```bash
mkdir -p output/demo-artifacts/specbuddy-video/hyperframes/assets/voice
cp output/demo-artifacts/specbuddy-video/assets/voice/scene-*.wav \
  output/demo-artifacts/specbuddy-video/hyperframes/assets/voice/
```

Measure duration and silence:

```bash
for f in output/demo-artifacts/specbuddy-video/assets/voice/scene-*.wav; do
  printf '%s ' "$f"
  ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$f"
  ffmpeg -hide_banner -nostats -i "$f" -af volumedetect -f null - 2>&1 | rg 'mean_volume|max_volume'
done
```

Do not proceed if a WAV is near-silent, implausibly short, or longer than its scene duration minus 1.5 seconds.

## HyperFrames Audio Mounting

Add one audio tag per scene under the composition root. Use a dedicated audio track index that does not overlap visual clips:

```html
<audio id="vo-01" data-start="1" data-duration="5.077" data-track-index="9" data-volume="1" src="assets/voice/scene-01.wav"></audio>
```

Set:

- `data-start`: scene start plus 1 second.
- `data-duration`: measured WAV duration, rounded to 3 decimals.
- `data-track-index`: a track that does not overlap visual scene clips.
- `src`: path relative to the composition HTML.

Regenerate captions from measured starts and durations, not from old silent-video timing:

```srt
1
00:00:01,000 --> 00:00:06,077
SpecBuddy helps teams catch weak requirements before a coding agent starts building.
```

## Render Verification

Run the check gate:

```bash
npx --yes hyperframes@0.7.107 check . --json
```

Render from the composition directory:

```bash
npx --yes hyperframes@0.7.107 render . \
  --quality high \
  --resolution landscape \
  --output ../../specbuddy-demo-final.mp4 \
  --skill product-launch-video \
  --no-best-effort
```

Verify streams:

```bash
ffprobe -v error \
  -show_entries stream=codec_type,codec_name,width,height,duration \
  -show_entries format=duration,size \
  -of default=noprint_wrappers=1 \
  output/demo-artifacts/specbuddy-demo-final.mp4
```

Expected voiceover render: H.264 video, 1920x1080, about 90 seconds, plus AAC audio.

Extract rendered verification frames, rebuild a labeled contact sheet, and inspect it visually before reporting success.
