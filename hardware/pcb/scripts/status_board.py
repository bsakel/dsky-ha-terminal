"""DSKY status-light board. Board coords = LED-splitter frame + (20, 20). Front (F.Cu) faces the lenses."""
import sys, json; sys.path.insert(0, '.')
from kgen import Board, Part, Router, write_pcb

OX, OY = 20.0, 20.0
P = lambda x, y: (x + OX, y + OY)
X0, Y0, X1, Y1 = -0.51, -0.95, 59.94, 105.16
LEFT, RIGHT = 13.715, 45.72
ROWS = [6.255, 21.845, 36.96, 52.07, 67.18]
LAMPS_L = ["UPLINK ACTY", "NO ATT", "STBY", "KEY REL", "OPR ERR"]
LAMPS_R = ["TEMP", "GIMBAL LOCK", "PROG", "RESTART", "TRACKER"]
LCSC = dict(led="C2761795", c100n="C14663", c10u="C15850", r330="C23138")


def build():
    b = Board("status_board", [[P(X0, Y0), P(X1, Y0), P(X1, Y1), P(X0, Y1)]])
    leds = [(LEFT, y, 0, LAMPS_L[i]) for i, y in enumerate(ROWS)] + [(RIGHT, y, 180, LAMPS_R[4 - i]) for i, y in enumerate(ROWS[::-1])]
    for k, (cx, cy, deg, lamp) in enumerate(leds, start=1):
        dout = f"D_{k + 1}" if k < 10 else ""
        b.add(Part(f"D{k}", "WS2812B_5050", *P(cx, cy), deg, value="WS2812B", lcsc=LCSC["led"], mpn="WS2812B-B/T",
                   nets={"1": "+5V", "2": dout, "3": "GND", "4": f"D_{k}"}))
        capx = cx + 6.0 if deg == 0 else cx - 6.0
        b.add(Part(f"C{k}", "C_0603", *P(capx, cy), 90, value="100nF", lcsc=LCSC["c100n"], mpn="CC0603KRX7R9BB104",
                   nets={"1": "GND", "2": "+5V"}))
        b.texts.append((lamp, *P(cx, cy + 4.4 if deg == 0 else cy + 4.4), "F.SilkS", 0.9, 0))
    b.add(Part("C11", "C_0805", *P(24.5, 24.5), 0, value="10uF", lcsc=LCSC["c10u"], mpn="CL21A106KAYNNNE", nets={"1": "+5V", "2": "GND"}))
    b.add(Part("R1", "R_0603", *P(22.04, 10.0), 90, value="330R", lcsc=LCSC["r330"], mpn="0603WAF3300T5E", nets={"1": "DIN_IN", "2": "D_1"}))
    b.add(Part("J1", "Conn_1x03_P2.54", *P(19.5, 18.0), 0, value="+5V DIN GND", nets={"1": "+5V", "2": "DIN_IN", "3": "GND"}, assembled=False))
    for i, (x, y) in enumerate([(3, 101.5), (56.4, 101.5), (3, 82), (56.4, 82)]):
        b.add(Part(f"H{i + 1}", "Hole_2.2", *P(x, y), 0))
    b.texts += [("DSKY STATUS LIGHTS", *P(30, 92), "B.SilkS", 1.5, 0), ("rev 1.0", *P(30, 95), "B.SilkS", 1.0, 0),
                ("+5V  DIN  GND", *P(22.04, 21.0), "B.SilkS", 0.8, 0)]
    return b


def route(b):
    r = Router(b, grid=0.2, via_cost=10.0)
    def targets(net):
        t = []
        for p in b.parts:
            for pd in p.fp.pads:
                if pd.num and p.nets.get(pd.num) == net:
                    x, y = p.pad_world(pd); ls = [l for l in ("F.Cu", "B.Cu") if l in p.pad_layers(pd) or "*.Cu" in p.pad_layers(pd)]
                    t.append((x, y, ls))
        return t
    order = [f"D_{k}" for k in range(1, 11)] + ["DIN_IN", "GND", "+5V"]
    for net in order:
        T = targets(net)
        if len(T) < 2: continue
        w = b.R["power"] if net in ("GND", "+5V") else b.R["track"]
        paths, fail = r.route(net, T, w)
        if paths is None:
            print("FAILED", net, fail); return False
        for x, y, ls in T:
            i, j = r.cell(x, y); cx, cy = r.pos(i, j)
            r.stub(net, x, y, cx, cy, ls[0], w)
        r.commit(net, paths, w)
        print("routed", net, len(paths), flush=True)
    return True


if __name__ == "__main__":
    b = build()
    ok = route(b)
    b.zones.append(("GND", "B.Cu", [P(X0 + 0.5, Y0 + 0.5), P(X1 - 0.5, Y0 + 0.5), P(X1 - 0.5, Y1 - 0.5), P(X0 + 0.5, Y1 - 0.5)]))
    errs = b.check()
    con = b.connectivity()
    print("clearance errors:", len(errs)); [print("  ", e) for e in errs[:15]]
    print("unconnected nets:", {k: v for k, v in con.items() if v != 1})
    out = sys.argv[1]
    write_pcb(b, out + "/status_board.kicad_pcb", "status_board.kicad_sch", "DSKY status-light board")
    import pickle; pickle.dump(b, open(out + "/status_board.pkl", "wb"))
