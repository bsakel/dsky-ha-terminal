"""DIY (hand-wired, Option B) schematic in KiCad + a wiring diagram image. Usage: diy.py <repo_root>"""
import sys, os; sys.path.insert(0, '.')
from ksch import Placed, write_sch
from build_all import project_files, snap
from keyboard_board import KEYS, GPIO_ROW, GPIO_COL

ROOT = sys.argv[1]
D = f"{ROOT}/hardware/diy"
os.makedirs(D, exist_ok=True)
LAMPS = ["UPLINK ACTY", "NO ATT", "STBY", "KEY REL", "OPR ERR", "TRACKER", "RESTART", "PROG", "GIMBAL LOCK", "TEMP"]

parts = []
gp_net = {g: f"ROW{i}" for i, g in enumerate(GPIO_ROW)}
gp_net.update({g: f"COL{i}" for i, g in enumerate(GPIO_COL)})
pin_of = {"5V": "23", "GND": "22", "GP14": "15", "GP15": "16", "GP26": "17", "GP27": "18", "GP28": "19", "GP29": "20",
          "GP9": "10", "GP10": "11", "GP11": "12", "GP12": "13", "GP13": "14"}
u1 = {pin_of[g]: n for g, n in gp_net.items()}
u1.update({"23": "+5V", "22": "GND", pin_of["GP14"]: "LED_3V3"})
parts.append(Placed("RP2040-Zero", "U1", snap(45), snap(80), "RP2040-Zero", nets=u1))
for i, (lab, X, Y, r, c, rr) in enumerate(KEYS, start=1):
    x, y = snap(100 + c * 30), snap(50 + r * 30)
    parts.append(Placed("SW", f"SW{i}", x, y, lab, nets={"1": f"COL{c}", "2": f"KD{i}"}))
    parts.append(Placed("D", f"D{i}", x + snap(12.7), y + snap(10.16), "1N4148", nets={"2": f"KD{i}", "1": f"ROW{r}"}))
parts.append(Placed("R", "R1", snap(80), snap(160), "330R", nets={"1": "LED_3V3", "2": "LED_D1"}))
for k in range(1, 11):
    parts.append(Placed("WS2812B_Mini", f"LED{k}", snap(100 + (k - 1) * 25.4), snap(160), LAMPS[k - 1],
                        nets={"DI": f"LED_D{k}", "DO": f"LED_D{k + 1}" if k < 10 else "", "5V": "+5V", "G": "GND"}))
parts.append(Placed("RPiZero", "U2", snap(80), snap(215), "Raspberry Pi Zero 2 W", nets={"PWR": "PI_5V", "USB": "USB_LINK", "GPIO": "HYPERPIXEL"}))
parts.append(Placed("HyperPixel", "DS1", snap(180), snap(215), "HyperPixel 4.0 Touch", nets={"GPIO": "HYPERPIXEL"}))
parts.append(Placed("USBC_In", "J1", snap(30), snap(215), "USB-C 5 V in (back plate)", nets={"V": "PI_5V", "G": "GND"}))
notes = [("Hand-wired build (Option B). Same matrix and pins as the PCB version, so the firmware is identical.\n"
          "Keys: 3 x 7 matrix, diode cathode (band) towards the ROW wire. ROW0 = GP28, ROW1 = GP29, ROW2 = GP15.\n"
          "COL0..COL6 = GP9, GP10, GP11, GP12, GP13, GP26, GP27.  Status lights: GP14 -> 330R -> LED1 DIN, chained LED1 -> LED10.\n"
          "LED order: left column top->bottom (LED1-5), then right column bottom->top (LED6-10).\n"
          "USB_LINK: short USB cable from the RP2040-Zero USB-C to the Pi Zero micro-USB DATA port (powers the RP2040 and LEDs).\n"
          "PI_5V: USB-C panel socket on the back plate -> Pi Zero micro-USB PWR port. Keep LED brightness low in firmware.", 20, 235, 1.5)]
root = write_sch(f"{D}/diy_wiring.kicad_sch", "diy_wiring", parts, "DSKY hand-wired build (Option B)", notes, paper="A3")
project_files(D, "diy_wiring", root)
open(f"{D}/fp-lib-table", "w").write('(fp_lib_table\n  (version 7)\n  (lib (name "dsky")(type "KiCad")(uri "${KIPRJMOD}/../pcb/lib/dsky.pretty")(options "")(descr ""))\n)\n')
open(f"{D}/sym-lib-table", "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "dsky")(type "KiCad")(uri "${KIPRJMOD}/../pcb/lib/dsky.kicad_sym")(options "")(descr ""))\n)\n')

# ------------------------------------------------------------------ wiring diagram image
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
fig, ax = plt.subplots(figsize=(16, 11)); ax.set_xlim(0, 160); ax.set_ylim(0, 110); ax.axis("off")
INK, ROWC, COLC, LEDC, PWR = "#1f2937", "#dc2626", "#2563eb", "#059669", "#f59e0b"
ax.text(2, 106, "DSKY HA terminal - hand-wired build (Option B)", fontsize=17, weight="bold", color=INK)
ax.text(2, 102.5, "Same matrix and pins as the PCB version: one firmware for both builds.", fontsize=10, color="#4b5563")
# keyboard matrix
gx0, gy0, dxg, dyg = 44, 88, 15.0, 13
ax.text(gx0 - 2, 98.6, "Key matrix (3 rows x 7 columns), switch -> diode -> row; diode band (cathode) on the ROW side", fontsize=10, color=INK)
grid = {}
for (lab, X, Y, r, c, rr) in KEYS: grid[(r, c)] = lab
for c in range(7):
    x = gx0 + c * dxg
    ax.plot([x, x], [gy0 + 3, gy0 - 2 * dyg - 4], color=COLC, lw=2)
    ax.text(x, gy0 + 4.5, f"COL{c}\n{GPIO_COL[c]}", ha="center", fontsize=8.5, color=COLC, weight="bold")
for r in range(3):
    y = gy0 - r * dyg - 5
    ax.plot([gx0 - 6, gx0 + 6 * dxg + 9], [y, y], color=ROWC, lw=2)
    ax.text(gx0 - 7, y, f"ROW{r}  {GPIO_ROW[r]}", ha="right", va="center", fontsize=8.5, color=ROWC, weight="bold")
    for c in range(7):
        if (r, c) not in grid: continue
        x, yk = gx0 + c * dxg, gy0 - r * dyg
        ax.add_patch(FancyBboxPatch((x + 1.2, yk - 2.2), 7, 4.4, boxstyle="round,pad=0.3", fc="#f3f4f6", ec=INK, lw=1))
        ax.text(x + 4.7, yk, grid[(r, c)], ha="center", va="center", fontsize=8, weight="bold", color=INK)
        ax.plot([x, x + 1.2], [yk, yk], color=COLC, lw=1.5)
        ax.plot([x + 8.2, x + 9.5, x + 9.5], [yk, yk, y + 1.2], color=INK, lw=1)
        ax.plot([x + 8.5, x + 10.5, x + 9.5, x + 8.5], [y + 1.2, y + 1.2, y, y + 1.2], color=INK, lw=1)
        ax.plot([x + 8.5, x + 10.5], [y, y], color=INK, lw=1.6)
        ax.plot([x + 9.5, x + 9.5], [y, y], color=ROWC)
# RP2040
ax.add_patch(FancyBboxPatch((3, 49), 22, 37, boxstyle="round,pad=0.5", fc="#e0e7ff", ec=INK, lw=1.4))
ax.text(14, 83.5, "RP2040-Zero", ha="center", fontsize=11, weight="bold", color=INK)
pins = [("5V", PWR), ("GND", INK), ("GP14  LED data", LEDC)] + [(f"{g}  ROW{i}", ROWC) for i, g in enumerate(GPIO_ROW)] + [(f"{g}  COL{i}", COLC) for i, g in enumerate(GPIO_COL)]
for k, (t, cc) in enumerate(pins):
    ax.text(5, 80 - k * 2.15, t, fontsize=8.3, color=cc, weight="bold")
ax.text(14, 50.0, "USB-C -> Pi Zero (data)", ha="center", fontsize=7.5, color="#4b5563")
# LED chain
ly = 33; ax.text(3, 44, "Status lights: WS2812B mini boards, one data chain", fontsize=10, color=INK)
order = [(0, i) for i in range(5)] + [(1, 4 - i) for i in range(5)]
for k, (col, row) in enumerate(order):
    x = 12 + k * 14.2
    ax.add_patch(Circle((x, ly), 3.2, fc="#d1fae5", ec=LEDC, lw=1.5))
    ax.text(x, ly, f"LED{k + 1}", ha="center", va="center", fontsize=7.5, weight="bold")
    ax.text(x, ly - 5.5, LAMPS[k], ha="center", fontsize=6.8, color="#374151")
    if k < 9: ax.annotate("", xy=(x + 11, ly), xytext=(x + 3.2, ly), arrowprops=dict(arrowstyle="->", color=LEDC, lw=1.4))
ax.annotate("GP14 -> 330R -> DIN", xy=(8.8, ly + 1.5), xytext=(2, 41), fontsize=8, color=LEDC, arrowprops=dict(arrowstyle="->", color=LEDC))
ax.plot([12, 12 + 9 * 14.2], [ly + 5, ly + 5], color=PWR, lw=1.5); ax.text(140, ly + 5.8, "+5V (RP2040 5V pin)", fontsize=7.5, color=PWR, ha="right")
ax.plot([12, 12 + 9 * 14.2], [ly - 8.5, ly - 8.5], color=INK, lw=1.5); ax.text(140, ly - 10.5, "GND", fontsize=7.5, color=INK, ha="right")
ax.text(12, 21, "Left column top->bottom = LED1-5, right column bottom->top = LED6-10 (as seen from the front).", fontsize=8, color="#4b5563")
# Pi + power
for (x, w, t) in [(3, 30, "USB-C panel socket\n(back plate)"), (48, 34, "Raspberry Pi Zero 2 W"), (100, 40, "HyperPixel 4.0 Touch\n(on the Pi GPIO header)")]:
    ax.add_patch(FancyBboxPatch((x, 4), w, 10, boxstyle="round,pad=0.4", fc="#fef3c7" if x == 3 else "#e0e7ff", ec=INK))
    ax.text(x + w / 2, 9, t, ha="center", va="center", fontsize=9, weight="bold", color=INK)
ax.annotate("", xy=(48, 9), xytext=(33.4, 9), arrowprops=dict(arrowstyle="->", color=PWR, lw=2)); ax.text(40.5, 11, "5 V -> PWR port", fontsize=7.5, ha="center", color=PWR)
ax.annotate("", xy=(100, 9), xytext=(82.4, 9), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.5)); ax.text(91, 11, "40-pin GPIO", fontsize=7.5, ha="center")
ax.plot([3.0, 1.0, 1.0, 65.0], [50.0, 50.0, 17.0, 17.0], color="#6b7280", lw=1.4)
ax.annotate("", xy=(65, 14.6), xytext=(65, 17.0), arrowprops=dict(arrowstyle="->", color="#6b7280", lw=1.4))
ax.text(66, 17.6, "USB cable: RP2040 USB-C <-> Pi micro-USB DATA port", fontsize=7.5, color="#6b7280")
plt.savefig(f"{D}/diy_wiring.png", dpi=150, bbox_inches="tight"); plt.savefig(f"{D}/diy_wiring.svg", bbox_inches="tight")
print("ok")
