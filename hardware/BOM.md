# Bill of materials

This covers the whole HA terminal: printed parts, fasteners, and electronics for both build options.

- **Option A – Custom PCBs.** A factory-assembled keyboard board plus a status-light board, ordered as one snap-apart panel.
- **Option B – Hand-wired.** No custom PCBs: WS2812B mini boards, through-hole diodes and wire.

Everything else is common to both builds. The part names match the component names in `cad/DSKY_HA_Terminal.step`.

## 1. Printed parts

PETG or PLA. Use clear or translucent filament for the lenses.

| Qty | Part | Build | Notes |
|---:|---|---|---|
| 1 | 2004739A Front chassis | common | Print face down. |
| 1 | 2004968E Mid frame – front half | common | Print face down (about 470 mm² of support). |
| 1 | 2004968E Mid frame – back half | common | Print with the split face on the bed. Bosses are bridged. |
| 1 | 2004919E Module plate | common | |
| 1 | 1006315A Seal plate | common | |
| 1 | 1006315G Display housing (HyperPixel) | common | |
| 1 | 1006315G Display cover (HyperPixel) | common | |
| 1 | HyperPixel spacer (long) | common | |
| 1 | Zero spacer (short) | common | |
| 1 | 1006387D Status light housing | common | |
| 1 | 1006387D Status light cover | common | |
| 10 | Status light lens | common | Clear or translucent. Print flat. |
| 1 | LED splitter | common | Light-tight. Use black or white opaque filament. |
| 19 | Key body | common | Gateron LP 2.0 stem (MX-style cross). |
| 19 | Key caps 1005022-001…019 | common | One cap per legend. |
| 1 | Stand cheek (left) | common | |
| 1 | Stand cheek (right) | common | Mirrored copy of the left cheek. |
| 1 | Stand foot bar | common | |
| 1 | Stand ledge bar | common | |
| 1 | Stand top bar | common | |
| 1 | Switch plate (low profile) | A | |
| 6 | Keyboard spacer | A | Fits between the keyboard PCB and the back plate. |
| 1 | Back plate | A | |
| 1 | Switch plate (with pillars) | B | The pillars carry the back plate. |
| 1 | LED holder | B | Holds the 10 mini boards behind the splitter. |
| 1 | Back plate + RP2040 cradle | B | |

All parts fit a 220 × 220 mm bed. The mid frame was split so that both halves print with little or no support.

To get STL files, open the STEP file in Fusion 360. For each body, choose *Save As Mesh* (or *3D Print*).

## 2. Fasteners

| Qty | Item | Used for |
|---:|---|---|
| 8 | M3 × 35 socket cap | Front chassis through the mid frame |
| 12 | M3 × 16 socket cap | Display module (6), status-light module (6) |
| +6 | M3 × 16 socket cap | **B only:** switch plate pillars |
| 13 | M3 × 12 button head | Seal plate / module plate (countersunk seats) |
| +6 | M3 × 12 button head | **A only:** keyboard PCB through the spacers |
| 8 | M3 × 6 button head | Back plate |
| 8 | M3 × 12 socket cap | Stand |
| 2 | M4 × 12 + M4 nut | Stand pivot pegs |
| 1 each | M2.5 × 16, M2.5 × 10, M2.5 × 5 socket cap | Pi Zero / HyperPixel stack |
| 2 | M2.5 standoff, M-F, 8.5 mm | Pi Zero / HyperPixel stack |
| 39 | Heat-set insert M3, 5 mm long (5.2 mm hole) | Mid frame (27), module plate (12) |
| 8 | Heat-set insert M3, 4 mm long (4.1 mm hole) | Mid frame, back plate screws |
| 5 | Dowel pin 3 × 8 mm | Aligning the two mid-frame halves (glue or press-fit) |

## 3. Electronics – common

| Qty | Item | Notes |
|---:|---|---|
| 1 | Raspberry Pi Zero 2 W | |
| 1 | Pimoroni HyperPixel 4.0 Touch (rectangular) | Plugs onto the Pi GPIO header. |
| 19 | Gateron low-profile 2.0 switches (KS-33) | From the Keychron S1. |
| 1 | RP2040-Zero (Waveshare) | Keyboard and LED controller. Connects to the Pi over USB. |
| 1 | Short USB-C ↔ micro-USB cable | RP2040 USB-C to the Pi **data** port. A 90° plug helps. |
| 1 | USB-C panel-mount socket (5 V in) | Feeds the Pi **PWR** port. Use a 5 V / 2.5 A+ supply. |
| 1 | 3-wire cable, about 10 cm | Keyboard board ↔ status board (+5V, DIN, GND). |

## 4. Electronics – Option A (custom PCBs)

These come from the panel in `pcb/panel` (230 × 106 mm, 2 layers, 1.6 mm). The factory places only the SMD parts below. You solder the hot-swap sockets, the RP2040-Zero and the two 3-pin connectors.

| Qty | Ref | Part | LCSC | Assembled by |
|---:|---|---|---|---|
| 10 | D101–D110 | WS2812B (5050) | C2761795 | JLCPCB |
| 19 | D1–D19 | 1N4148W (SOD-123) | C81598 | JLCPCB |
| 11 | C1, C101–C110 | 100 nF 0603 | C14663 | JLCPCB |
| 2 | C2, C111 | 10 µF 0805 | C15850 | JLCPCB |
| 2 | R1, R101 | 330 Ω 0603 | C23138 | JLCPCB |
| 1 | U2 | 74AHCT1G125 (SOT-23-5), 3.3 V → 5 V data buffer | C7484 | JLCPCB |
| 19 | SW1–SW19 | Gateron low-profile hot-swap socket | – | you |
| 1 | U1 | RP2040-Zero, soldered by its castellated edge to the back | – | you |
| 2 | J1, J101 | 3-pin, 2.54 mm (header or direct wires) | – | you |

The machine-readable files are in `pcb/jlcpcb/<board>/*_BOM.csv` and `*_CPL.csv`.

## 5. Electronics – Option B (hand-wired)

| Qty | Item | Notes |
|---:|---|---|
| 10 | WS2812B mini round boards (about 10 mm) | One per status lamp, chained. |
| 19 | 1N4148 diode (through-hole) | One per key, band towards the row wire. |
| 1 | 330 Ω resistor | In series with the LED data line. |
| – | 26–28 AWG wire (several colours), heat-shrink | |

The wiring is in `diy/diy_wiring.kicad_sch`, with a picture in `diy/diy_wiring.png`.
