# Lifeline Node case (final, "Hex Facets")

Pi 5 + AI HAT+ home-monitor node. Two printed parts. Built in build123d; every part is checked against a hardware model (0 collisions) before export.

## Print it (Bambu P1S, 0.4 nozzle, Textured PEI)

| File | Orientation | Material | Time (0.20 mm) |
|---|---|---|---|
| `print/final_body.stl` | upright, floor on the bed | PLA-CF | about 4 h 04 m, 138 g |
| `print/final_lid_bambu.3mf` | already flipped, top face on the bed | 4 colours (below) | about 2 h 21 m |

The lid file is a sliced Bambu project. Open it in Bambu Studio, map the 4 slots to real spools, and print.

| Slot | Part | Colour |
|---|---|---|
| 1 | lid | black PLA-CF |
| 2 | LAND logo | white PLA |
| 3 | NVIDIA logo | green PLA |
| 4 | State Farm logo | red PLA |

- The logos are inlaid flush, 0.6 mm deep (the first 3 layers), so all colour changes happen in those 3 layers. A prime tower sits beside the lid.
- **The lid needs an AMS.** Without one, print the lid in black only.
- `print/final_lid.3mf` is the same lid unsliced: one object made of 4 parts, each on its own filament slot.

## What goes where

**Body**
- **Pi 5:** sits on the floor, held by corner walls with no screws. The HAT-kit screw heads under the board drop into cups in the floor.
- **Wall openings:**
  - one merged slot for USB-C and HDMI;
  - a USB slot on the +x wall for the SDR's extension cable;
  - side vents.
- **30 mm 5 V fan:** drops into floor rails. Add a dab of hot glue at the top.
- **HIBOX3070-K speaker:** sits in a cradle on the -x wall, behind a hex grille. It fastens with M3 screws from outside.

**Lid**
- **NeoPixel Ring 12 (Adafruit 1643):** in the centre pocket, with 4 wire holes (IN, OUT, PWR, GND).
- **Camera Module 3:** in rails on the left side.
- **HC-SR501 PIR:** flush in a recess on the right, wired from below.

**Lid screws:** 4 × M3 × 1/4" into M3 heat-set inserts in the body.

**Ring wiring:**
- 5 V to pin 2 or 4, GND to pin 6.
- DIN to GPIO10 (pin 19), through a 330 Ω resistor. GPIO18 is taken by I2S audio.

## Not measured yet (datasheet or estimated values)

| Part | Value used | If it's off |
|---|---|---|
| Fan | 30 × 30 × 7 mm | must be 30 × 30 to fit the rails |
| PIR PCB | 32.4 × 24.1 × 1.2 mm | thicker means it sits proud |
| NeoPixel ring | 3.2 mm thick | thicker means it sits proud |
| Speaker | 30 × 70 × 17 mm | wrong size won't fit the cradle |

## Rebuild from source

You need Python with `build123d` and `trimesh`.

```
cd hardware/node
python build_final.py              # checks fits, writes out/final_body.stl and out/final_lid.3mf
python tools/slice_lid_colors.py   # Bambu Studio CLI: slices the 4-colour lid for the P1S into out/final_lid_bambu.3mf
```

- `node_single.py` holds the base case. It imports the Pi geometry from `../case/pi5_aihat_case.py`.
- `node_v5.py` holds the final design, including the speaker, the ring, the PIR and the logo inlays.
- The logo artwork is in `logos/`.
