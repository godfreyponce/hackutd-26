# Voice check-in (#14)

The box speaks and listens. It does not decide anything. The agent (#15) sends a `say`; this service speaks the text. If the `say` has `listen_s`, it listens that many seconds, turns the answer into `ok`, `help` or `no_answer`, and sends one `heard`. The agent owns the tries, the alarm rule and the script text.

## Setup (once, with internet)

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r software/voice/requirements.txt
.venv/bin/python -m software.voice --download
```

`--download` saves the offline voice to `~/.cache/hackutd-voice/` and Moonshine to the Hugging Face cache. After that the offline mode runs with Wi-Fi off.

## Run

```bash
.venv/bin/python -m software.voice            # online if ELEVENLABS_API_KEY is set, else offline
.venv/bin/python -m software.voice --offline  # Piper speaks, Moonshine listens, no network
.venv/bin/python -m software.voice --text     # prints the line, reads a typed answer
```

`HUB_URL` picks the bus (default `ws://localhost:8765`).

## Modes

- **Online:** ElevenLabs text-to-speech (`eleven_flash_v2_5`) and speech-to-text (`scribe_v2`). If a request fails, that line falls back to Piper or Moonshine, so cutting the Wi-Fi mid-demo keeps working. With no `ELEVENLABS_API_KEY` it logs `MOCK/OFFLINE: no ELEVENLABS_API_KEY` and runs offline.
- **Offline:** Piper or Kokoro speaks, Moonshine (`moonshine/base`) listens. `moonshine/tiny` missed the "help me" fixture.

## Voice

One setting each. Set the env var, or change the default in `engines.py`.

- `OFFLINE_VOICE`: `piper:<voice>` or `kokoro:<voice>`, for example `kokoro:af_heart` or `piper:en_US-ryan-high`. Default `piper:en_US-lessac-medium`. Run `--download` after a change.
- `ELEVEN_VOICE_ID`: an ElevenLabs voice id. Default `ljX1ZrXuDIIRVcmiVSyR`, picked by Godfrey from the Voice Library. It must be in the account's My Voices.
- **Text:** no audio. A timeout counts as silence.

Why not Eleven Realtime v1 Mini: it is a speech-to-speech agent. Its docs don't promise that it says a fixed line word for word, and they list no event that hands us a transcript of the answer. The box must say the agent's exact line, and the agent must get a transcript.

## Classifier

`classify.py` is a keyword match, no LLM. In order:
1. A help word (help, hurt, emergency, can't get up) is `help`.
2. Any negation (no, nope, not, never, -n't) is `help`, so "I'm not okay" and "no" never become `ok`.
3. yes, yeah, yep, okay, ok, fine, alright is `ok`. "Good" is not: room chatter misheard as "Good boy" became `ok` in a live test.
4. Anything else, silence included, is `no_answer`.

## Microphone

If macOS blocks the mic, the recording is pure digital silence and the log says which app needs access (System Settings, Privacy & Security, Microphone). The answer then counts as `no_answer`.

The listener trims the quiet around the answer before Moonshine reads it. The gate is relative to the room's noise floor. It was checked against a real recording on a MacBook with input volume at 27%. If a spoken answer comes back empty, raise the input volume in System Settings, Sound, Input.

## Tests

```bash
.venv/bin/python -m pytest software/voice
```

The offline speech-to-text tests use fixtures made with macOS `say` and converted to 16 kHz mono WAV with `afconvert`, plus one real room-noise recording.
