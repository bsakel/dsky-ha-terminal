# DSKY HA terminal: project context

An Apollo AGC DSKY lookalike that works as a Home Assistant control terminal.

The mechanical design is derived from [MKme/AGC_DSKY_Replica](https://github.com/MKme/AGC_DSKY_Replica) (GPL-3.0). The hardware below was designed with Claude in an earlier session. This repo is where the firmware and software get built.

## Hardware (designed, not yet built or ordered)

- **Raspberry Pi Zero 2 W** drives a **FYSETC CTP40** display (4.0" 800×480 DPI touch, a HyperPixel 4.0 clone). Specs and drivers: https://github.com/FYSETC/FYSETC-CTP40
- **RP2040-Zero** (Waveshare) handles the keys and status lights. It connects to the Pi with **one USB cable**: RP2040 USB-C to the Pi's micro-USB data port. That cable powers the RP2040 and carries all data.
  - There is only one microcontroller because the Pi Zero has a single USB data port.
- **19 Gateron low-profile 2.0 switches** (KS-33, MX-style stem) and **10 WS2812B status lights**.
- **Two build options**, with identical pins, so one firmware covers both:
  - **A – custom PCBs** (`hardware/pcb`): keyboard board plus status board on one JLCPCB panel. The LED data line is buffered 3.3 V → 5 V by a 74AHCT1G125.
  - **B – hand-wired** (`hardware/diy`): WS2812B mini boards and 1N4148 diodes. The LED data line is unbuffered.

### Pin map

| Signal | RP2040 GPIO |
|---|---|
| ROW0 / ROW1 / ROW2 | GP28 / GP29 / GP15 |
| COL0 … COL6 | GP9, GP10, GP11, GP12, GP13, GP26, GP27 |
| WS2812B data | GP14 |
| On-board RGB LED | GP16 |

The diodes are **COL2ROW**: drive a column, read the rows (with pull-downs).

| | COL0 | COL1 | COL2 | COL3 | COL4 | COL5 | COL6 |
|---|---|---|---|---|---|---|---|
| ROW0 | VERB | + | 7 | 8 | 9 | CLR | ENTR |
| ROW1 | NOUN | − | 4 | 5 | 6 | PRO | RSET |
| ROW2 | – | 0 | 1 | 2 | 3 | KEY REL | – |

### LED chain order

Index 0 is the first LED after GP14.

The chain runs down the left column, then up the right column, as seen from the front:

| Index | Lamp |
|---:|---|
| 0 | UPLINK ACTY |
| 1 | NO ATT |
| 2 | STBY |
| 3 | KEY REL |
| 4 | OPR ERR |
| 5 | TRACKER |
| 6 | RESTART |
| 7 | PROG |
| 8 | GIMBAL LOCK |
| 9 | TEMP |

All 10 LEDs at full white draw about 600 mA from the Pi's USB port. **Firmware must limit brightness.**

## Repo layout

- `hardware/cad/`: the STEP models.
  - `DSKY_HA_Terminal.step` holds both build options as components.
  - `DSKY_Original_Build.step` is the original replica.
- `hardware/pcb/`: KiCad 8 projects (keyboard board, status board, panel), shared `lib/`, JLCPCB BOM/CPL files and `scripts/`.
  - The scripts are the Python generators that produced the boards. Regenerating overwrites hand edits.
- `hardware/diy/`: the hand-wired schematic (KiCad) and a wiring diagram.
- `hardware/BOM.md`: the full bill of materials.
- `firmware/`: RP2040 firmware. Not started.
- `software/`: Pi-side software. Not started.

## Open hardware items (don't assume these are done)

- **KiCad.** DRC and ERC pass with no errors on both boards, the panel and the DIY schematic (as of Nov 2026).
  - Still to do: check the Gateron hot-swap and RP2040-Zero footprints against the real parts, and check LED and diode rotation in JLCPCB's preview.
  - The board copy of RP2040-Zero differs from the library copy; decide which is right.
  - The full pending list is in `README.md` under *Pending steps*.
- **KiCad files are KiCad 8 format.** The dev machine has KiCad 10, which converts them when saving. Patch the files as text, or ask before upgrading. Use KiCad's bundled Python (`C:\Program Files\KiCad\10.0\bin\python.exe`); there's no Python on the PATH.
- **3D model.** The keyboard PCB in the model still has old MX-style holes and lacks the RP2040 tab. The KiCad board is the reference.
- **CTP40 fit.** The screen fits, with two caveats:
  - The CTP40's active area sits about 1.5 mm further along the long axis than the HyperPixel model, relative to the mounting holes. The two display-housing holes need to move by that much.
  - The CTP40's thickness isn't published. The model allows 4.0 mm from the back of the board to the front of the glass, so it needs measuring.

## Software and firmware: decisions not made yet

Discuss these with Vasilis before choosing:

- **Firmware stack:** CircuitPython, MicroPython, Arduino-Pico, or KMK/QMK.
- **Pi ↔ RP2040 protocol:** USB CDC serial, HID + serial, or something else. Key events go up to the Pi; lamp states come down to the RP2040.
- **Pi UI:** a kiosk browser (for example, a Home Assistant dashboard) or a native app. It needs a DSKY-style VERB/NOUN interaction mapped to Home Assistant services.
- **CTP40 driver on the Zero 2 W:** FYSETC ships Pi3/Pi4 overlays. Check what works on the current Raspberry Pi OS.

## Working with Vasilis

- Keep responses short, and cover one decision at a time. Long multi-topic answers make it hard for him to discuss things in depth.
- He's a C# developer by background, also working in Python, Go and TypeScript.
- He runs Home Assistant at home.
- He wants 3D-printed parts that need minimal or no supports. His printer bed is 220–256 mm.
