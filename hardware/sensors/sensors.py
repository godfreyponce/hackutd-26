"""Box sensors -> hub: MPU-6050 (quake), BMP280 (indoor temperature/pressure), PIR (motion).

Wiring: hardware/WIRING.md. I2C bus 1: MPU-6050 0x68, BMP280 0x76. PIR DO on GPIO17.

Events (contract #19 + the proposal on #19):
  {"type":"quake","peak_g":0.42}                       existing contract; the agent starts a check-in
  {"type":"indoor","temp_f":73.4,"temp_c":23.0,"pressure_hpa":1000.1}   every INDOOR_EVERY_S
  {"type":"pir","motion":true}                          rising edge of the PIR output
  {"type":"heat","temp_f":92.1,"reason":"over 90 F"}    too hot, or a fast rise (heater, fire); the agent starts a check-in

Run: HUB_URL=ws://localhost:8765 python3 hardware/sensors/sensors.py   (--dry-run prints only)
"""
import argparse
import asyncio
import json
import os
import struct
import sys
import time

from smbus2 import SMBus

MPU, BMP, PIR_GPIO = 0x68, 0x76, 17
SAMPLE_HZ = 100
QUAKE_G = 0.15          # deviation from the calibrated resting |a| that counts as shaking
QUAKE_SAMPLES = 5       # ... this many samples over the threshold within QUAKE_WINDOW_S
QUAKE_WINDOW_S = 0.5
QUAKE_REPORT_S = 1.5    # collect the peak for this long after the trigger
QUAKE_COOLDOWN_S = 15
INDOOR_EVERY_S = 15
PIR_COOLDOWN_S = 3
HEAT_F = float(os.environ.get("HEAT_F", 90))          # absolute limit
HEAT_RISE_F = float(os.environ.get("HEAT_RISE_F", 3))  # ... or this many F within HEAT_RISE_S
HEAT_RISE_S = 60
HEAT_EVERY_S = 2
HEAT_COOLDOWN_S = 120


def log(*a):
    print(*a, file=sys.stderr, flush=True)


class Mpu:
    def __init__(self, bus):
        self.bus = bus
        bus.write_byte_data(MPU, 0x6B, 0)  # wake
        time.sleep(0.1)
        rest = [self.mag() for _ in range(200)]  # ~2 s, board must be still at start
        self.base = sum(rest) / len(rest)
        log(f"MPU-6050 resting |a| = {self.base:.3f} g (subtracted as baseline)")

    def mag(self):
        ax, ay, az = struct.unpack(">hhh", bytes(self.bus.read_i2c_block_data(MPU, 0x3B, 6)))
        time.sleep(1 / SAMPLE_HZ)
        return (ax * ax + ay * ay + az * az) ** 0.5 / 16384

    def deviation(self):
        return abs(self.mag() - self.base)


class Bmp:
    """BMP280 with the Bosch datasheet floating-point compensation."""

    def __init__(self, bus):
        self.bus = bus
        chip = bus.read_byte_data(BMP, 0xD0)
        if chip != 0x58:
            log(f"BMP280 chip id {chip:#x}, expected 0x58")
        (self.T1, self.T2, self.T3, self.P1, self.P2, self.P3, self.P4, self.P5, self.P6,
         self.P7, self.P8, self.P9) = struct.unpack("<HhhHhhhhhhhh", bytes(bus.read_i2c_block_data(BMP, 0x88, 24)))
        bus.write_byte_data(BMP, 0xF5, 0xA0)  # 1 s standby
        bus.write_byte_data(BMP, 0xF4, 0x27)  # temp x1, pressure x1, normal mode

    def read(self):
        r = self.bus.read_i2c_block_data(BMP, 0xF7, 6)
        adc_p = (r[0] << 12) | (r[1] << 4) | (r[2] >> 4)
        adc_t = (r[3] << 12) | (r[4] << 4) | (r[5] >> 4)
        v1 = (adc_t / 16384 - self.T1 / 1024) * self.T2
        v2 = ((adc_t / 131072 - self.T1 / 8192) ** 2) * self.T3
        tf = v1 + v2
        v1 = tf / 2 - 64000
        v2 = v1 * v1 * self.P6 / 32768 + v1 * self.P5 * 2
        v2 = v2 / 4 + self.P4 * 65536
        v1 = (self.P3 * v1 * v1 / 524288 + self.P2 * v1) / 524288
        v1 = (1 + v1 / 32768) * self.P1
        p = 1048576 - adc_p
        p = (p - v2 / 4096) * 6250 / v1
        p += (self.P9 * p * p / 2147483648 + p * self.P8 / 32768 + self.P7) / 16
        return tf / 5120, p / 100


async def hub_sender(url, q):
    import websockets
    while True:
        try:
            async with websockets.connect(url) as ws:
                log(f"hub connected: {url}")
                while True:
                    await ws.send(json.dumps(await q.get()))
        except Exception as e:  # report and retry; never silent
            log(f"hub error ({url}): {e!r}; retrying in 2 s")
            await asyncio.sleep(2)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print events, send nothing")
    args = ap.parse_args()
    url = os.environ.get("HUB_URL", "ws://localhost:8765")
    q = asyncio.Queue()

    def emit(msg):
        print(json.dumps(msg), flush=True)
        if not args.dry_run:
            q.put_nowait(msg)

    if not args.dry_run:
        asyncio.create_task(hub_sender(url, q))
    loop = asyncio.get_running_loop()
    bus = SMBus(1)
    mpu = await loop.run_in_executor(None, Mpu, bus)
    bmp = Bmp(bus)
    from gpiozero import DigitalInputDevice
    pir = DigitalInputDevice(PIR_GPIO, pull_up=False)

    hits, last_quake, next_indoor, pir_was, last_pir = [], 0.0, 0.0, False, 0.0
    temps, next_heat, last_heat = [], 0.0, -HEAT_COOLDOWN_S
    while True:
        now = time.monotonic()
        dev = await loop.run_in_executor(None, mpu.deviation)
        if dev > QUAKE_G:
            hits = [t for t in hits if now - t < QUAKE_WINDOW_S] + [now]
            if len(hits) >= QUAKE_SAMPLES and now - last_quake > QUAKE_COOLDOWN_S:
                peak, end = dev, now + QUAKE_REPORT_S
                while time.monotonic() < end:
                    peak = max(peak, await loop.run_in_executor(None, mpu.deviation))
                emit({"type": "quake", "peak_g": round(peak, 2)})
                last_quake, hits = time.monotonic(), []
        if now >= next_heat:
            f = bmp.read()[0] * 9 / 5 + 32
            temps = [(t, v) for t, v in temps if now - t <= HEAT_RISE_S] + [(now, f)]
            rise = f - min(v for _, v in temps)
            reason = f"over {HEAT_F:g} F" if f >= HEAT_F else f"rose {rise:.1f} F in {HEAT_RISE_S} s" if rise >= HEAT_RISE_F else None
            if reason and now - last_heat > HEAT_COOLDOWN_S:
                emit({"type": "heat", "temp_f": round(f, 1), "reason": reason})
                last_heat = now
            next_heat = now + HEAT_EVERY_S
        if now >= next_indoor:
            c, hpa = bmp.read()
            emit({"type": "indoor", "temp_f": round(c * 9 / 5 + 32, 1), "temp_c": round(c, 2), "pressure_hpa": round(hpa, 1)})
            next_indoor = now + INDOOR_EVERY_S
        motion = bool(pir.value)
        if motion and not pir_was and now - last_pir > PIR_COOLDOWN_S:
            emit({"type": "pir", "motion": True})
            last_pir = now
        pir_was = motion
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
