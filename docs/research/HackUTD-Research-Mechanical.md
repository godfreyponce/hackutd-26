---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, mechanical]
---

# Research: Mechanical (stepper pan/tilt + turntable)

Part of [HackUTD-2026](../HackUTD-2026.md). Agent research, 2026-11-07. [u] = unverified. Companion: [HackUTD-Research-Embedded](HackUTD-Research-Embedded.md).

**Bottom line:** start from **Printables 1180365** (CC0, NEMA 17, 3:1 pulley, STEP files you can edit in Fusion). Use **GT2 20T→60T (3:1) on pan**. Tilt carries only a ~4 g camera, so direct drive is fine there. Limit pan to **±180° with soft limits and a cable loop**; skip the slip ring.

## Ranked designs
| # | Design | License | Extra parts (from page) | Camera fit | Notes |
|---|---|---|---|---|---|
| 1 | [Pan Tilt Mount (NEMA 17)](https://www.printables.com/model/1180365), talal_malik | CC0 | 3:1 pulley system. **No BOM published** | Flat top plate; "DSLR plate in future" | 8 STL + STEP (base, side plates, motor plate). Editable, no attribution needed. Check belt and pulley sizes in the STEP at 12 PM |
| 2 | [Camera Pan/Tilt Head](https://www.printables.com/model/184076), suromark | CC BY | 2× NEMA 17, 2× GT2-280 + 1× GT2-158 closed belts (6 mm), 20T pulleys (5 mm and 8 mm bore), **4× 608ZZ**, 2× MR115, 5 mm × 30 and 8 mm × 55 shafts, M8 60–100 bolt, M3/M4 | Generic head | **No supports**, 15% infill, 0.2 mm. Best match for parts on hand, but the closed-loop belt lengths are specific |
| 3 | [Pan & Tilt w/NEMA17](https://www.printables.com/model/22610) (remix of [buffcleb Camera Rotator](https://www.thingiverse.com/thing:1396552)) | CC BY-NC | Per axis: **4× 608**, 5070 thrust bearing, M3×50/17, 32.5 mm Al spacer, 5/16" rod, GT2 322 mm (45T, 2:1) or 286 mm (22T, ~4:1) | 1/4-20 plate | Proven, but "work in progress / BOM may have errors." Too many odd parts for 24 h |
| 4 | [Digital Bird PTZ head](https://www.printables.com/model/326746-camera-pan-tilt-head-digital-bird) | CC BY-NC | GT2 360/200 mm closed belts, 20T NEMA 17 pulley, **61806 + 6811 + 625 bearings**, many M5 | Arca/DSLR, 3.5 kg tilt | Continuous 360° pan. Overkill; the bearings aren't on hand. **Reject** |
| 5 | [OpenTurret](https://github.com/cubanmakers/OpenTurret) | MIT | NEMA 17 0.9°, TMC2209, unspecified bearings/belts | Laser, not camera | Slip ring is a to-do, "experimental." Reference only |

Also seen: [isaac879 Pan-Tilt-Mount](https://github.com/isaac879/Pan-Tilt-Mount) (pan 144:17, tilt 64:21, TMC2208, Hall homing, about 20°/s pan at 1/16 µstep. Slider-centric, license type not shown). [Pi camera NEMA bracket](https://www.printables.com/model/1059150) (CC BY-SA, M2 screws, snaps around the motor) is a ready-made tilt camera clip.

**Turntable:**
1. [Turntable on NEMA 17 (42-40)](https://www.printables.com/model/1347100), poconoco. CC BY-NC. **Direct drive, 4× 608 on M5×15**, TPU track, TMC2225. 4 walls, 5 top/bottom layers, 25% infill. **Uses your 608s. Pick this.**
2. [Adafruit Motorized Turntable](https://www.printables.com/model/1169349). CC BY-SA. IKEA Snudda lazy susan + TMC2209 + KB2040. Needs the IKEA part.

## Direct drive vs GT2 3:1
| | Direct | GT2 20T→60T |
|---|---|---|
| Resolution, 1/16 µstep | 0.1125°/µstep. At 66° HFOV over 1280 px (≈19 px/°) that is ≈2 px | 0.0375° (≈0.7 px) |
| Backlash | Only shaft/coupling slop | Belt stretch. HowToMechatronics measured about 25 arcmin on a tensioned 16:1 printed belt drive, lower than printed planetary/cycloidal drives |
| Torque at output | 1× | 3× (less overshoot when loaded) |
| Speed | Highest | ÷3. 60°/s pan = 1,600 steps/s, within AccelStepper's `setMaxSpeed(2000)` |
| Smoothness | Microstep ripple shows directly, and a low-speed resonance "buzz" [u] | Belt damps the ripple. Smoother slow tracking |
| Parts | None | 20T pulley, belt, 60T pulley (print the large one) |

**Recommendation:**
- **Pan:** 3:1 belt. It carries the tilt motor (about 280 g [u]) and gains the most from damping.
- **Tilt:** direct drive. Fall back to direct drive on pan too if belts can't be found by about 1 PM.
- **Printed pulley rules** ([JU belts](https://mechanics.ju.se/MachineElements/belts.html)):
  - Buy the motor pulley and print only the big one, axis vertical.
  - A 20T GT2 pitch diameter is about 12.22 mm.
  - Keep **≥6 teeth in mesh**.
  - Tension until midspan deflects 2–3 mm. Printed frames creep, so re-tension after an hour.

## Cable management
- **±180° pan, soft limits, service loop:** zero cost. AccelStepper position limits, plus a loose helical loop through the hollow pan axis. **Do this.**
- **Slip ring:** [Adafruit 1196](https://www.adafruit.com/product/1196) has 12 wires, 2 A, 22 mm OD, a 44 mm flange, 300 RPM. It's **out of stock** and can't pass the Pi camera's CSI ribbon. You'd have to move the Pi onto the rotating stage. Not worth it.
- The Pi 5 uses the 22-pin CSI connector ([RPi camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html)). Buy a **≥300 mm 22→15-pin cable** [u length] and route it with a gentle bend, never a crease.

## Base: Pi 5 + monitor
- **Pi 5:** board 85×56 mm, holes **58×49 mm**, 3.5 mm from the edge, Ø2.7 mm (M2.5) ([mechanical drawing](https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf)). Use M2.5 standoffs, or print 5 mm bosses and self-tap M2.5. **M3 won't fit**; drill the holes to M3 only as a last resort [u].
- **Camera Module 3:** 25×24×11.5 mm, holes match Cam Module 2, HFOV 66° (Wide 102°).
- **Monitor:** a printed easel or VESA-style back plate on the base's front face. Measure the monitor's holes first [u]. Put the base's heavy mass (Pi, PSU) low and toward the back so the head doesn't tip.
- Give the Pi its active cooler and a vent slot, because the Hailo plus a 24 h run means heat.

## Print settings (Bambu)
- **PLA** for everything. PETG only for parts near motors that run hot for 24 h. NEMA 17 cases can reach 50–70 °C, which is near PLA's softening point [u]. Print motor mounts in PETG, or run the motors at 70% current (already the plan).
- Use the **0.20 mm Standard** profile (0.24–0.28 mm for the base): 3–4 walls, 15–25% gyroid infill, 4–5 top/bottom layers.
- **Fit tolerances:**
  - Bearing seats: +0.1–0.15 mm for a 608 press fit. Print a test ring first (10 min).
  - Holes: M3 clearance 3.3–3.4 mm.

**Print budget [u, estimate; verify in Bambu Studio]:**
| Plate | Parts | Est. time |
|---|---|---|
| 0, 1:30 PM | 608 fit ring + 60T pulley test | 0:20 |
| 1, 2:00 PM | Pan base + pan plate | 2:30–3:30 |
| 2 | Tilt yoke + motor plates + camera bracket | 1:30–2:30 |
| 3 | Pi/monitor base | 2:30–4:00 |
| 4 (optional) | Turntable base/top + TPU track | 3:00–4:00 |

The critical path is 1 → 2. The head can be done by about 8 PM, with the base printing in parallel if a second printer is free.

## Micro Center shopping list (if missing)
Couldn't verify the Dallas store inventory (site blocked). Check before driving.
- **GT2 6 mm belt** (open, cut and joined, or a closed loop) + **20T 5 mm-bore pulleys** ×2 [u stock]. 3D-printer kits often bundle 20T pulley + idler + 5 m belt [u].
- **608ZZ bearings** (also sold as skate bearings) [u].
- **M2.5 standoffs** for the Pi, M5×15 bolts for the turntable, and a 22→15-pin Pi 5 camera cable.

## Assembly gotchas
- **Flat on the D-shaft:** pulley grub screws go **on the flat**. Add a drop of thread-lock.
- **Bearings carry the load:** don't let the motor shaft carry the pan load. Use a 608 or thrust surface, and keep the motor torque-only.
- **Balance tilt:** center of mass on the tilt axis, so a 4 g camera needs no holding current.
- **Zero by hand:** center by hand at power-up and call that 0 (per the embedded note). Mark the zero position with a Sharpie line.
- **Isolate vibration:** rubber feet. A 24 h demo table gets bumped.
- **Bench-test the gear ratio:** test `steps/deg = 200·16·3/360 = 26.67` on the bench before tracking.

## Sources
Printables model pages (read via Printables API): [1180365](https://www.printables.com/model/1180365) · [184076](https://www.printables.com/model/184076) · [22610](https://www.printables.com/model/22610) · [326746](https://www.printables.com/model/326746-camera-pan-tilt-head-digital-bird) · [1347100](https://www.printables.com/model/1347100) · [1169349](https://www.printables.com/model/1169349) · [1059150](https://www.printables.com/model/1059150) · [thingiverse 1396552](https://www.thingiverse.com/thing:1396552) · [thingiverse 4547074](https://www.thingiverse.com/thing:4547074) · [isaac879 GitHub](https://github.com/isaac879/Pan-Tilt-Mount) · [OpenTurret](https://github.com/cubanmakers/OpenTurret) · [Structables open-source PT head](https://structables.lunar.icu/Open-Source-Pan-Tilt-Head-for-DIY-Motion-Control) · [HowToMechatronics drives](https://howtomechatronics.com/how-it-works/what-is-the-best-3d-printed-drive-for-your-next-robotic-project/) · [JU belts](https://mechanics.ju.se/MachineElements/belts.html) · [Adafruit 1196](https://www.adafruit.com/product/1196) · [Adafruit 1251](https://www.adafruit.com/product/1251) · [RPi camera docs](https://www.raspberrypi.com/documentation/accessories/camera.html) · [Pi 5 mechanical drawing](https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf)
