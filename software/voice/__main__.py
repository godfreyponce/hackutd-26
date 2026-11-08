"""python -m software.voice [--online|--offline|--text|--download]. Reads HUB_URL and ELEVENLABS_API_KEY."""

import argparse
import asyncio
import os
import sys


def log(line: str):
    print(f"[voice] {line}", flush=True)


def pick_mode(flag: str | None, env) -> tuple[str, str | None]:
    """Return (mode, warning). Online without a key falls back to offline."""
    if flag in ("offline", "text"):
        return flag, None
    if not env.get("ELEVENLABS_API_KEY"):
        return "offline", "MOCK/OFFLINE: no ELEVENLABS_API_KEY"
    return "online", None


def build_engine(mode: str):
    from software.voice import engines

    if mode == "text":
        return engines.TextEngine()
    offline = engines.OfflineEngine(log)
    if engines.record(0.3, log) is not None:
        log("microphone works")
    if mode == "offline":
        return offline
    return engines.ElevenLabsEngine(os.environ["ELEVENLABS_API_KEY"], offline, log)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m software.voice")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--online", dest="mode", action="store_const", const="online", help="ElevenLabs (default)")
    group.add_argument("--offline", dest="mode", action="store_const", const="offline", help="Piper + Moonshine, no network")
    group.add_argument("--text", dest="mode", action="store_const", const="text", help="print lines, read typed answers")
    group.add_argument("--download", action="store_true", help="fetch the offline models once, then exit")
    args = parser.parse_args(argv)

    if args.download:
        os.environ["HF_HUB_OFFLINE"] = "0"
        from software.voice.engines import MODEL_DIR, download_models

        download_models()
        log(f"offline models ready in {MODEL_DIR} and the Hugging Face cache")
        return 0

    mode, warning = pick_mode(args.mode, os.environ)
    if warning:
        log(warning)
    log(f"mode: {mode}")

    from software.voice.engines import AlarmTone
    from software.voice.service import VoiceService

    url = os.environ.get("HUB_URL", "ws://localhost:8765")
    service = VoiceService(build_engine(mode), log, None if mode == "text" else AlarmTone())
    try:
        asyncio.run(service.run(url))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
