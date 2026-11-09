# Custom PCBs (Option A)

| Folder | What it is |
|---|---|
| `keyboard-board/` | 168 × 77 mm board with 19 Gateron LP hot-swap sockets, a diode per key and the RP2040-Zero on the back. |
| `status-board/` | 60 × 106 mm board with 10 WS2812B LEDs behind the status lenses. |
| `panel/` | Both boards in one 230 × 106 mm panel joined by two mouse-bite tabs. This is the file you order. |
| `lib/` | Project symbol and footprint libraries, used by all three projects through `${KIPRJMOD}/../lib`. |
| `jlcpcb/` | BOM and CPL (pick-and-place) files for JLCPCB assembly, one set per project. |
| `scripts/` | The Python generators that produced the boards. Only needed if you want to regenerate them. |

Both boards were routed and checked with the generator's own clearance and connectivity checks:

- 0.2 mm copper clearance and 0.4 mm to the board edge.
- No errors and no unconnected nets.

KiCad's DRC is still the final word.

## Before ordering (KiCad 8)

1. **Check the footprints against real parts.**
   - Open `lib/dsky.pretty` in the footprint editor.
   - **Gateron_LP_Hotswap.** Check it against your socket's datasheet: the centre hole is 5.1 mm, the two pin holes are 3.0 mm, and the pads are on the back. Print the board 1:1 on paper and lay a switch on it.
   - **RP2040-Zero.** Check the pad pitch and pin names against the Waveshare drawing. The module is soldered to the back by its castellated edge, with the USB-C pointing up out of the tab.
2. **Open each board.** Open `keyboard-board/keyboard_board.kicad_pro` and `status-board/status_board.kicad_pro`.
   - Press **B** to fill the zones. The GND pour on the back layer is defined but not filled.
   - Run **Inspect → Design Rules Checker** with *Test for parity between PCB and schematic* enabled.
   - Fix or accept anything it reports. Silkscreen-over-pad warnings are cosmetic.
3. **Open the panel.** Open `panel/dsky_panel.kicad_pcb`, fill the zones (B) and run DRC.
   - The panel has no schematic, so turn off schematic parity.
   - Nets carry a `K_` prefix (keyboard) or `S_` prefix (status), and status-board references are numbered from 100 so that they don't clash.
4. **Make the Gerbers.** Use *File → Fabrication Outputs → Gerbers* with JLCPCB's recommended settings, plus the drill files. Alternatively, install the **Fabrication Toolkit** plugin, which builds Gerbers, BOM and CPL in one click.
5. **Upload to JLCPCB.**
   - Board settings: 2 layers, 1.6 mm, HASL lead-free or ENIG, any colour.
   - **Assembly:** PCBA, top side. Upload `jlcpcb/panel/dsky_panel_BOM.csv` and `dsky_panel_CPL.csv`.
   - In the placement preview, **check the rotation of every part type**, especially the WS2812B LEDs: the notch (pin 1, VDD) must sit at the marked corner. The diode band must face the cathode mark. Rotate any part that is off in the preview; JLC applies your correction.
   - The hot-swap sockets, RP2040-Zero and connectors are marked *do not populate*. They are deliberately missing from the BOM, so JLC will not ask about them.

## Panel or separate boards?

JLCPCB treats a file containing several designs as a panel and may add a small "multiple designs" fee. Compare two quotes:

1. **The panel.** One board of 230 × 106 mm and one assembly setup.
2. **Two separate orders.** Two boards under 100 × 100 / 170 mm and two setups.

Assembly setup and extended-part fees usually make the panel the cheaper option. If they don't, the individual projects are ready to order on their own with their own BOM/CPL.

After delivery, snap the panel apart at the two mouse-bite tabs (pliers, then file the nubs flat).

## Hand assembly after delivery

1. **Hot-swap sockets** (back side): 19 of them, two pads each. Tin one pad, place the socket, then solder both pads.
2. **RP2040-Zero** (back side): line up the castellations with the pads and solder only the pins that are used. Those are 5V, GND, GP9–GP15 and GP26–GP29; soldering all of them is fine too.
3. **Status cable**, between J1 on the keyboard board and J101 (J1 on its own board) on the status board:
   - Pin 1: +5V
   - Pin 2: DIN
   - Pin 3: GND

## Pin map (same for both builds)

| Function | RP2040 GPIO |
|---|---|
| ROW0 (VERB, +, 7, 8, 9, CLR, ENTR) | GP28 |
| ROW1 (NOUN, −, 4, 5, 6, PRO, RSET) | GP29 |
| ROW2 (0, 1, 2, 3, KEY REL) | GP15 |
| COL0 … COL6 | GP9, GP10, GP11, GP12, GP13, GP26, GP27 |
| WS2812B data | GP14 (buffered to 5 V on Option A) |

The diodes go column → row (COL2ROW).
