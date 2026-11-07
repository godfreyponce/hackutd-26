# Pi 5 + AI HAT+ (26T) case: requirements plan (2026-11-07)

Coordinates: Pi 5 top view, origin = PCB corner at the micro-HDMI edge (y=0) and microSD edge (x=0).
GPIO along y=56, USB/Ethernet on x=85. z=0 = top of the case floor. All mm.

## Sources (primary)
- Pi 5 mechanical drawing: https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf
- AI HAT+ brief: https://datasheets.raspberrypi.com/ai-hat-plus/raspberry-pi-ai-hat-plus-product-brief.pdf
- HAT+ spec (15 mm min / 16 mm stack): https://datasheets.raspberrypi.com/hat/hat-plus-specification.pdf
- Active Cooler brief: https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-product-brief.pdf
- Camera Module 3 brief: https://datasheets.raspberrypi.com/camera/camera-module-3-product-brief.pdf
- Fan: 52Pi 4010 5V PWM 2-pack, Micro Center SKU 605634; 52Pi wiki F-0012 (GPIO-driven, M3x16 + nuts included)

## Hardware facts used
| Item | Value | Status |
|---|---|---|
| Pi PCB | 85 x 56, holes d2.7 at (3.5,3.5) (61.5,3.5) (3.5,52.5) (61.5,52.5) | drawing |
| PCB thickness | modelled 1.6 (worst case) | measure |
| USB-C / HDMI0 / HDMI1 centres | x 11.2 / 25.8 / 39.2, axis 3.2-3.4 above PCB | drawing |
| Ethernet / USB / USB centres | y 10.2 / 29.1 / 47.0, overhang 3 | drawing |
| USB stack height | 16.4 above PCB | scaled |
| Power button / LED | left edge y 18.4 / 13.3 | drawing |
| microSD | underside, left edge, y ~28.9, card sticks out ~2.25 | scaled |
| CAM/DISP 0+1 | x ~48.8 / 55.0, y 0.6-15.9 | scaled |
| AI HAT+ | 65 x 56.5, same holes, 16 mm stack, notch x 47.5-57.5 depth 16 over the CAM connectors, FFC slot left edge y 21-39 | drawing |
| Hailo-8 | 17 x 17 at x 22.5-39.5, y 18-35 | drawing/scaled |
| Fan | 40x40x10, 32 mm hole pattern, 5V, GPIO 5V/GND + PWM on GPIO18 | Micro Center listing + 52Pi wiki |
| Camera Module 3 | 25 x 23.86 x 1.12, lens 7.4 proud of PCB, connector 2.75 behind | brief |

## Requirements
1. Every port usable with real cables: USB-C, 2x micro-HDMI, 2x USB-A stacks, Ethernet, microSD, power button, LED visible.
2. AI HAT+ on the official 16 mm stack; Active Cooler fits underneath; PCIe ribbon not pinched.
3. 40 mm Micro Center fan over the Hailo-8, blowing down; fan cable reaches GPIO.
4. GPIO header usable with the lid on (jumper wires to the stepper MCU).
5. Camera ribbon exits through a slot; camera mount is a bolt-on module (optional).
6. Fasteners: M3 screws + M3 heat-set inserts only. No M2/M2.5 parts needed beyond the HAT kit.
7. Modular: base / lid / fan guard / camera bracket / camera cradle are separate, swappable parts.
8. Printable without supports on a Bambu (0.4 nozzle, PLA or PETG).
9. Tolerances: >=0.5 mm air around every component, 1 mm around the PCB, +0.75/side on port notches,
   insert holes d4.0 x 6.5-8 deep, M3 clearance d3.4, sliding fits +0.15-0.3/side.

## Architecture
- **Split line at z 24.5**, just above the HAT. Base walls carry all I/O; the right-side ports drop
  into open-top notches so the assembled Pi+HAT stack goes in straight down, then the lid closes the notch tops.
- **Base**: floor + walls + 4 corner towers with M3 inserts; 4 bosses with pockets for the HAT-kit
  screw heads/nuts under the Pi (locates the stack, no M2.5 into plastic).
- **Lid**: fan opening, fan insert bosses, GPIO slot, camera-ribbon slot over the HAT notch,
  stop posts that keep the stack from lifting, 2 inserts for the camera bracket.
- **Fan on top of the lid** with a guard; screws pass guard + fan into lid inserts.
- **Camera**: fork bracket (2x M3 into lid) + tilting cradle (2x M3 pivots into inserts, friction).

## Open items to measure on the real parts
Spacer length in the HAT kit, PCB thickness, header pin height above the HAT, insert outer diameter,
fan hole diameter, fan connector type.

## Build status (2026-11-07)
- Model: `pi5_aihat_case.py` (build123d) -> `out/*.step|stl`; `make_plate.py` -> `out/Pi5-AIHAT-Case_plate.3mf`.
- Interference check vs. a proxy Pi+HAT stack (ports, HAT, header pins, kit screw heads): 0.000 mm^3 for base, lid, camera.

## Fasteners
| Where | Qty | Part |
|---|---|---|
| Base towers (lid screws) | 4 | M3 insert + M3x10 |
| Lid fan bosses | 4 | M3 insert + M3x16 (52Pi kit includes M3x16) through guard + fan |
| Lid camera bosses | 2 | M3 insert + M3x8 (bracket) |
| Cradle pivots | 2 | M3 insert + M3x8 (tension = tilt friction) |

## Assembly
1. Heat-set all 12 inserts (4 base, 6 lid, 2 cradle) before anything else.
2. Build the Pi + Active Cooler + AI HAT+ stack with the kit hardware; drop it straight down into the base
   (screw heads/nuts seat in the boss pockets; ports drop into the right-side notches).
3. Close the lid (4x M3x10). Fan label side DOWN (blows into the case), guard on top, 4x M3x16.
4. Fan leads through the GPIO slot: 5V pin 4, GND pin 6, PWM GPIO18 (pin 12) per 52Pi wiki.
5. Optional camera: bracket on lid (2x M3x8), slide camera into cradle from the top, ribbon down through the lid slot
   to the CAM connector (route it before closing the lid).

## Assembly viewer
- Live: https://claude.ai/artifact/UAZPMmUuEyz29EhkhQrZD6 (private). Rebuild: `python export_viewer.py meshes.json`, then put the JSON into `out/viewer_template.html` where it says `__MESHES__`.

## Theme: HackUTD 2026 "Zero Day" (2026-11-07)
- Lid top: `> ZERO_DAY_` / `HACKUTD 2026` engraved 0.6 mm (Consolas, slashed zero), in the strip between fan and camera bracket; >=3.1 mm from every slot/hole. Reads from the USB side.
- Fan guard grille = a slashed zero (2.0 mm oval stroke, 2.4 mm slash).
- Back-wall vents are binary: tall = 1, short = 0, spelling ASCII `0` | `D` (0110000 1 1000100).
- 0.8 mm chamfer on the base bottom edge, 0.6 mm on the lid top edge (both bed faces: no overhang, no elephant foot).
