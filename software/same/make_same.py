"""Write a demo SAME alert as audio, only for a cable into our own decoder.

Never transmit it and never play it out loud: 47 CFR 11.45 bans simulated
EAS tones. Station HACKDEMO marks it as ours.

    python -m software.same.make_same OUT.wav [--header 'ZCZC-...-HACKDEMO-']

OUT ending in .raw writes headerless signed 16-bit little-endian audio.
Both are mono at 22050 Hz, the rate multimon-ng's EAS decoder reads.
"""

import argparse
import math
import re
import struct
import sys
import wave
from datetime import datetime, timezone

RATE = 22050
BAUD = 520 + 5 / 6     # 47 CFR 11.31: 520.83 bits per second
MARK = 2083 + 1 / 3    # bit 1
SPACE = 1562.5         # bit 0
PREAMBLE = bytes([0xAB] * 16)
AMPLITUDE = 12000
WARNING_TONE_HZ = 1050  # NOAA Weather Radio warning alarm tone
WARNING_TONE_S = 8      # 47 CFR 11.31 sets 8 s as the shortest attention signal
HEADER_RE = re.compile(r"ZCZC-[A-Z]{3}-[A-Z]{3}-\d{6}(-\d{6}){0,30}\+\d{4}-\d{7}-[ -~]{1,8}-")


def default_header(now: datetime) -> str:
    utc = now.astimezone(timezone.utc)
    return f"ZCZC-WXR-EQW-048113-048085+0030-{utc:%j%H%M}-HACKDEMO-"


def silence(seconds: float) -> list[int]:
    return [0] * int(RATE * seconds)


def tone(freq: float, seconds: float) -> list[int]:
    return [int(AMPLITUDE * math.sin(2 * math.pi * freq * n / RATE)) for n in range(int(RATE * seconds))]


def burst(text: str) -> list[int]:
    data = PREAMBLE + text.encode("ascii")
    bits = [(byte >> i) & 1 for byte in data for i in range(8)]  # LSB first
    out, phase = [], 0.0
    for k, bit in enumerate(bits):
        step = 2 * math.pi * (MARK if bit else SPACE) / RATE
        while len(out) < (k + 1) * RATE / BAUD:
            out.append(int(AMPLITUDE * math.sin(phase)))
            phase += step
    return out


def same_message(header: str) -> list[int]:
    audio = silence(1)
    for _ in range(3):
        audio += burst(header) + silence(1)
    audio += tone(WARNING_TONE_HZ, WARNING_TONE_S) + silence(2)
    for _ in range(3):
        audio += burst("NNNN") + silence(1)
    return audio


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", help="output file, .wav or .raw")
    parser.add_argument("--header", help="full SAME header (default: demo EQW for Dallas and Collin, now)")
    args = parser.parse_args(argv)
    header = args.header or default_header(datetime.now(timezone.utc))
    if not HEADER_RE.fullmatch(header):
        print(f"not a SAME header: {header!r}", file=sys.stderr)
        return 2
    if not args.out.endswith((".wav", ".raw")):
        print(f"output must end in .wav or .raw: {args.out}", file=sys.stderr)
        return 2
    audio = same_message(header)
    pcm = struct.pack(f"<{len(audio)}h", *audio)
    if args.out.endswith(".raw"):
        with open(args.out, "wb") as f:
            f.write(pcm)
    else:
        with wave.open(args.out, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(pcm)
    print(f"wrote {args.out}: {header}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
