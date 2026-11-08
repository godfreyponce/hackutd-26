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

- **Online:** ElevenLabs text-to-speech (`eleven_v4_turbo`) and speech-to-text (`scribe_v2`). If a request fails, that line falls back to Piper or Moonshine, so cutting the Wi-Fi mid-demo keeps working. With no `ELEVENLABS_API_KEY` it logs `MOCK/OFFLINE: no ELEVENLABS_API_KEY` and runs offline.
- **Offline:** Piper or Kokoro speaks, Moonshine (`moonshine/base`) listens. `moonshine/tiny` missed the "help me" fixture.

## Voice

One setting each. Set the env var, or change the default in `engines.py`.

- `OFFLINE_VOICE`: `piper:<voice>` or `kokoro:<voice>`, for example `kokoro:af_heart` or `piper:en_US-ryan-high`. Default `kokoro:am_liam`, picked by Godfrey from 18 samples. Run `--download` after a change.
- Offline speech plays at 90% speed (`OFFLINE_SPEED` in `engines.py`), the speed of the sample Godfrey picked.
- `ELEVEN_VOICE_ID`: an ElevenLabs voice id. Default `ljX1ZrXuDIIRVcmiVSyR`, picked by Godfrey from the Voice Library. It must be in the account's My Voices.
- **Text:** no audio. A timeout counts as silence.

## Audio tags

ElevenLabs gets an audio tag in front of each line, for example `[gently]` for `ask_retry_2`. The tags live in `ELEVEN_TAGS` in `engines.py`, keyed by the `say` message's `script_id`. A line with an unknown id gets no tag. The agent's text has no tags, so a tag never reaches the bus or the home screen. The offline voice never gets one, because it would read the tag out loud.

## Alarm tone

On `{"type":"checkin","state":"alarm"}` the box speaker plays `assets/alarm.wav` once, after the line it is speaking. The service keeps listening for later messages while the tone plays. A `reset` stops it. Text mode only logs it.

The alarm is fake. The tone plays only on the box. Nothing is called. `assets/alarm.wav` is a yelp siren, 3 s (owner pick). `assets/make_tones.py` makes the older candidates.

Why not Eleven Realtime v1 Mini: it is a speech-to-speech agent. Its docs don't promise that it says a fixed line word for word, and they list no event that hands us a transcript of the answer. The box must say the agent's exact line, and the agent must get a transcript.

## Classifier

`classify.py` is a keyword match, no LLM. In order:
1. A help word is `help`: help, hurt, emergency, ambulance, bleed or bleeding, blood (not "blood pressure" or "blood sugar"), injured or injury, paramedic, dizzy, can't, can barely or can hardly get up or breathe, fell or fallen (not "fell asleep", "fell back asleep" or "fallen asleep"), on the floor or ground (also the kitchen or bathroom floor), had a fall, heart attack, trouble breathing, hard to breathe, short of breath or shortness of breath, I slipped (not "slipped my mind", "slipped up" or "slipped out"), hit my head, need/get/call a doctor, fire or smoke (not a fire or smoke alarm or detector), pain, chest, faint, trapped, firefighter, fireman, 911 (also 9-1-1, 9 1 1, nine one one), call someone or somebody, save me. blood, pain, chest, faint, trapped, fire and smoke match only as whole words or listed forms (pains, painful, fainting, smokes and so on), so "painting", "fireplace", "Chester", "bloody" and "smoking" are not help. "Doctor", "breathe" and "call my" alone are not help, because ok replies use them ("my doctor said I'm fine", "I can breathe", "I'll call my daughter"). "Stuck" and "please come" are not help, for the same reason ("stuck in traffic", "please come in"). A missed help still reaches the alarm after 3 asks.
2. Any negation (no, nope, nah, not, never, cannot, -n't, and -nt words with no apostrophe such as cant, dont, wont, isnt) is `help`, so "I'm not okay" and "no" never become `ok`.
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
