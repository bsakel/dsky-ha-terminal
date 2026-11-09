"""DSKY keyboard board. Assembly frame (X right, Y up, mm) -> KiCad: (X + 1, 94 - Y). Front (F.Cu) faces the keycaps."""
import sys, json, pickle; sys.path.insert(0, '.')
from kgen import Board, Part, Router, write_pcb

K = lambda X, Y: (X + 1.0, 94.0 - Y)
COLS_X = [53.8, 78.525, 103.15, 127.775, 152.4]
ROW_Y = [62.95, 38.35, 13.75]
# (label, X, Y, row, col, socket rotation)
KEYS = [("VERB", 29.25, 50.75, 0, 0, 0), ("NOUN", 29.25, 26.0, 1, 0, 0),
        ("ENTR", 177.05, 50.75, 0, 6, 180), ("RSET", 177.05, 26.0, 1, 6, 180)]
for r, (labels, rotn) in enumerate([(["+", "7", "8", "9", "CLR"], 0), (["-", "4", "5", "6", "PRO"], 0), (["0", "1", "2", "3", "KEY REL"], 180)]):
    for c, lab in enumerate(labels):
        KEYS.append((lab, COLS_X[c], ROW_Y[r], r, c + 1, rotn))
MOUNTS = [(22.78, 38.282), (183.57, 38.282), (91.17, 7.54), (115.17, 7.54), (91.17, 69.68), (115.17, 69.68)]
GPIO_ROW = ["GP28", "GP29", "GP15"]
GPIO_COL = ["GP9", "GP10", "GP11", "GP12", "GP13", "GP26", "GP27"]
LCSC = dict(d="C81598", u="C7484", c100n="C14663", r330="C23138", c10u="C15850")
RP = dict(x=34.5, y=68.5)   # RP2040-Zero centre (assembly frame), USB-C towards +Y


def outline():
    pts = [(25, 4), (181, 4), (181, 10), (187, 10), (187, 68), (181, 68), (181, 74), (44.5, 74), (44.5, 81.0), (25, 81.0), (25, 68), (19, 68), (19, 10), (25, 10)]
    return [[K(x, y) for x, y in pts]]


def build():
    b = Board("keyboard_board", outline())
    for i, (lab, X, Y, r, c, rr) in enumerate(KEYS, start=1):
        b.add(Part(f"SW{i}", "Gateron_LP_Hotswap", *K(X, Y), rr, value=lab, nets={"1": f"COL{c}", "2": f"KD{i}"}, dnp=True, assembled=False))
        dx = 10.2 if rr == 0 else -10.2
        b.add(Part(f"D{i}", "D_SOD-123", *K(X + dx, Y), 90, value="1N4148W", lcsc=LCSC["d"], mpn="1N4148W",
                   nets={"1": f"ROW{r}", "2": f"KD{i}"}))
        b.texts.append((lab, *K(X, Y - 9.3 if rr == 0 else Y + 9.3), "B.SilkS", 1.0, 0))
    # RP2040-Zero on the back, castellated edges; pins by GPIO name
    u = b.add(Part("U1", "RP2040-Zero", *K(RP["x"], RP["y"]), 0, side="B", value="RP2040-Zero", dnp=True, assembled=False))
    gp = {pd.name: pd.num for pd in u.fp.pads}
    nets = {gp["5V"]: "+5V", gp["GND"]: "GND", gp["GP14"]: "LED_3V3"}
    for r, g in enumerate(GPIO_ROW): nets[gp[g]] = f"ROW{r}"
    for c, g in enumerate(GPIO_COL): nets[gp[g]] = f"COL{c}"
    u.nets = nets
    b.add(Part("U2", "SOT-23-5", *K(37.0, 61.5), 0, value="74AHCT1G125", lcsc=LCSC["u"], mpn="SN74AHCT1G125DBVR",
               nets={"1": "GND", "2": "LED_3V3", "3": "GND", "4": "LED_5V", "5": "+5V"}))
    b.add(Part("C1", "C_0603", *K(37.0, 65.0), 0, value="100nF", lcsc=LCSC["c100n"], mpn="CC0603KRX7R9BB104", nets={"1": "+5V", "2": "GND"}))
    b.add(Part("C2", "C_0805", *K(31.0, 76.5), 0, value="10uF", lcsc=LCSC["c10u"], mpn="CL21A106KAYNNNE", nets={"1": "+5V", "2": "GND"}))
    b.add(Part("R1", "R_0603", *K(37.0, 68.0), 0, value="330R", lcsc=LCSC["r330"], mpn="0603WAF3300T5E", nets={"1": "LED_5V", "2": "LED_DIN"}))
    b.add(Part("J1", "Conn_1x03_P2.54", *K(47.5, 72.2), 0, value="to status board", nets={"1": "+5V", "2": "LED_DIN", "3": "GND"}, dnp=True, assembled=False))
    for i, (x, y) in enumerate(MOUNTS):
        b.add(Part(f"H{i + 1}", "MountingHole_M3", *K(x, y), 0))
        kx, ky = K(x, y)
        b.keepouts.append(("F.Cu", kx - 3.1, ky - 3.1, kx + 3.1, ky + 3.1))   # screw head (front)
        b.keepouts.append(("B.Cu", kx - 3.4, ky - 3.4, kx + 3.4, ky + 3.4))   # spacer (back)
    kx0, ky0 = K(RP["x"] - 6.0, RP["y"] + 9.5); kx1, ky1 = K(RP["x"] + 6.0, RP["y"] - 9.0)
    b.keepouts.append(("B.Cu", kx0, ky0, kx1, ky1))                            # under the module body
    b.texts += [("DSKY KEYBOARD rev 1.0", *K(103.15, 26.5), "B.SilkS", 1.5, 0),
                ("+5V DIN GND", *K(50.04, 76.6 - 2.0), "B.SilkS", 0.8, 0),
                ("Rows GP28 GP29 GP15 / Cols GP9-13 GP26 GP27 / LED GP14", *K(103.15, 23.5), "B.SilkS", 0.9, 0)]
    return b


def route(b, order=None):
    r = Router(b, grid=0.2, via_cost=8.0)
    def targets(net):
        t = []
        for p in b.parts:
            for pd in p.fp.pads:
                if pd.num and p.nets.get(pd.num) == net:
                    x, y = p.pad_world(pd); lay = p.pad_layers(pd)
                    t.append((x, y, [l for l in ("F.Cu", "B.Cu") if l in lay or "*.Cu" in lay]))
        return t
    nets = order or (["GND", "+5V", "LED_3V3", "LED_5V", "LED_DIN"] + [f"KD{i}" for i in range(1, 20)] + [f"ROW{i}" for i in range(3)] + [f"COL{i}" for i in range(7)])
    failed = []
    for net in nets:
        T = targets(net)
        if len(T) < 2: continue
        w = b.R["power"] if net in ("GND", "+5V") else b.R["track"]
        paths, fail = r.route(net, T, w)
        if paths is None:
            failed.append((net, fail)); print("FAILED", net, fail, flush=True); continue
        for x, y, ls in T:
            i, j = r.cell(x, y); cx, cy = r.pos(i, j); r.stub(net, x, y, cx, cy, ls[0], w)
        r.commit(net, paths, w)
        print("routed", net, flush=True)
    return failed


if __name__ == "__main__":
    b = build()
    failed = route(b)
    errs = b.check(); con = b.connectivity()
    print("failed:", failed)
    print("clearance errors:", len(errs)); [print("  ", e) for e in errs[:20]]
    print("unconnected nets:", {k: v for k, v in con.items() if v != 1})
    out = sys.argv[1]
    write_pcb(b, out + "/keyboard_board.kicad_pcb", "keyboard_board.kicad_sch", "DSKY keyboard board")
    pickle.dump(b, open(out + "/keyboard_board.pkl", "wb"))
