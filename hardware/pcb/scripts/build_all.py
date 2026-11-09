"""Write KiCad projects (schematic + PCB), shared libraries, snap-apart panel, JLCPCB BOM/CPL. Usage: build_all.py <repo_root>"""
import sys, os, json, copy, pickle, csv
sys.path.insert(0, '.')
import kgen
from kgen import write_pcb, write_fp_lib, Part, LIB
import ksch
from ksch import Placed, write_sch, write_sym_lib

ROOT = sys.argv[1]
PCB = f"{ROOT}/hardware/pcb"
SYM_OF = {"WS2812B_5050": "WS2812B", "C_0603": "C", "C_0805": "C", "R_0603": "R", "D_SOD-123": "D", "Gateron_LP_Hotswap": "SW",
          "Conn_1x03_P2.54": "Conn3", "SOT-23-5": "74AHCT1G125", "RP2040-Zero": "RP2040-Zero", "MountingHole_M3": "Hole", "Hole_2.2": "Hole"}


def project_files(d, name, root_uuid):
    os.makedirs(d, exist_ok=True)
    pro = {"meta": {"filename": f"{name}.kicad_pro", "version": 1},
           "board": {"design_settings": {"rules": {"min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.5, "min_via_annular_width": 0.1,
                                                   "min_through_hole_diameter": 0.3, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
                                                   "min_copper_edge_clearance": 0.3, "min_silk_clearance": 0.0}}},
           "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3,
                                          "diff_pair_gap": 0.25, "diff_pair_width": 0.2, "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12}],
                            "meta": {"version": 3}},
           "sheets": [[root_uuid, "Root"]] if root_uuid else []}
    json.dump(pro, open(f"{d}/{name}.kicad_pro", "w"), indent=2)
    open(f"{d}/fp-lib-table", "w").write('(fp_lib_table\n  (version 7)\n  (lib (name "dsky")(type "KiCad")(uri "${KIPRJMOD}/../lib/dsky.pretty")(options "")(descr "DSKY project footprints"))\n)\n')
    open(f"{d}/sym-lib-table", "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "dsky")(type "KiCad")(uri "${KIPRJMOD}/../lib/dsky.kicad_sym")(options "")(descr "DSKY project symbols"))\n)\n')


def sch_parts_from_board(b, layout):
    out = []
    for p in b.parts:
        x, y = layout(p)
        out.append(Placed(SYM_OF[p.fp.name], p.ref, x, y, value=p.value, fp="dsky:" + p.fp.name, lcsc=p.lcsc, mpn=p.mpn,
                          nets=p.nets, dnp=p.dnp, uuid_=p.sym_uuid))
    return out


def snap(v): return round(v / 2.54) * 2.54


# ---------------------------------------------------------------- status board
def status(b):
    def layout(p):
        r = p.ref
        if r.startswith("D"): k = int(r[1:]); return snap(40 + (k - 1) * 25.4), snap(60)
        if r.startswith("C") and r != "C11": k = int(r[1:]); return snap(40 + (k - 1) * 25.4), snap(90)
        if r == "C11": return snap(40), snap(120)
        if r == "R1": return snap(80), snap(120)
        if r == "J1": return snap(130), snap(120)
        if r.startswith("H"): k = int(r[1:]); return snap(180 + k * 15), snap(120)
    parts = sch_parts_from_board(b, layout)
    notes = [("Status-light board: 10 x WS2812B in one chain (left column top->bottom, then right column bottom->top).\n"
              "Lamps: D1 UPLINK ACTY, D2 NO ATT, D3 STBY, D4 KEY REL, D5 OPR ERR, D6 TRACKER, D7 RESTART, D8 PROG, D9 GIMBAL LOCK, D10 TEMP.\n"
              "J1 is hand-soldered (wires or a 3-pin header) and connects to J1 on the keyboard board.", 20, 140, 1.5)]
    d = f"{PCB}/status-board"; os.makedirs(d, exist_ok=True)
    root = write_sch(f"{d}/status_board.kicad_sch", "status_board", parts, "DSKY status-light board", notes)
    project_files(d, "status_board", root)
    write_pcb(b, f"{d}/status_board.kicad_pcb", "status_board.kicad_sch", "DSKY status-light board")
    return parts


# ---------------------------------------------------------------- keyboard board
def keyboard(b, keys):
    pos = {}
    for i, (lab, X, Y, r, c, rr) in enumerate(keys, start=1):
        pos[f"SW{i}"] = (snap(100 + c * 30), snap(50 + r * 30)); pos[f"D{i}"] = (snap(100 + c * 30 + 12.7), snap(50 + r * 30 + 10.16))
    pos.update({"U1": (snap(45), snap(80)), "U2": (snap(45), snap(160)), "C1": (snap(80), snap(160)), "C2": (snap(80), snap(175)),
                "R1": (snap(110), snap(160)), "J1": (snap(140), snap(160))})
    for k in range(1, 7): pos[f"H{k}"] = (snap(200 + k * 15), snap(175))
    parts = sch_parts_from_board(b, lambda p: pos[p.ref])
    notes = [("Keyboard board: 19 keys in a 3 x 7 matrix, diodes column-to-row (COL2ROW).\n"
              "Rows: ROW0 = GP28, ROW1 = GP29, ROW2 = GP15.  Columns: COL0..COL6 = GP9, GP10, GP11, GP12, GP13, GP26, GP27.\n"
              "LED data: GP14 -> 74AHCT1G125 (3.3 V to 5 V) -> 330R -> J1 pin 2 -> status board.\n"
              "Hand-soldered by you: SW1-SW19 (Gateron low-profile hot-swap sockets), U1 (RP2040-Zero), J1.", 20, 195, 1.5)]
    d = f"{PCB}/keyboard-board"; os.makedirs(d, exist_ok=True)
    root = write_sch(f"{d}/keyboard_board.kicad_sch", "keyboard_board", parts, "DSKY keyboard board", notes, paper="A3")
    project_files(d, "keyboard_board", root)
    write_pcb(b, f"{d}/keyboard_board.kicad_pcb", "keyboard_board.kicad_sch", "DSKY keyboard board")


# ---------------------------------------------------------------- panel (both boards, snap-apart tabs with mouse bites)
def panel(kb, sb):
    P = kgen.Board("panel", [])
    dx, dy = 190.0 - 19.49, 0.0 - 19.05
    for p in kb.parts:
        q = copy.copy(p); q.nets = {k: "K_" + v for k, v in p.nets.items() if v}; P.parts.append(q)
    for p in sb.parts:
        q = copy.copy(p); q.x, q.y = p.x + dx, p.y + dy
        q.ref = p.ref[0] + str(100 + int(''.join(ch for ch in p.ref if ch.isdigit())))
        q.nets = {k: "S_" + v for k, v in p.nets.items() if v}; P.parts.append(q)
    P.segs = [(a, b_, c, d, w, l, "K_" + n) for (a, b_, c, d, w, l, n) in kb.segs] + \
             [(a + dx, b_ + dy, c + dx, d + dy, w, l, "S_" + n) for (a, b_, c, d, w, l, n) in sb.segs]
    P.vias = [(x, y, "K_" + n) for (x, y, n) in kb.vias] + [(x + dx, y + dy, "S_" + n) for (x, y, n) in sb.vias]
    P.texts = kb.texts + [(t, x + dx, y + dy, l, s, r) for (t, x, y, l, s, r) in sb.texts] + [("Snap apart at the mouse bites", 189.0, 62.75, "F.SilkS", 0.8, 90)]
    W = 190.0 + (79.94 - 19.49)
    tabs = [(48.0, 53.0), (72.5, 77.5)]   # upper tab between the ENTR and RSET sockets, clear of their pads
    outer = [(26, 90), (182, 90), (182, 84), (188, 84), (188, tabs[1][1]), (190, tabs[1][1]), (190, 106.11), (W, 106.11), (W, 0.0), (190, 0.0),
             (190, tabs[0][0]), (188, tabs[0][0]), (188, 26), (182, 26), (182, 20), (45.5, 20), (45.5, 13), (26, 13), (26, 26), (20, 26), (20, 84), (26, 84)]
    slot = [(188, tabs[0][1]), (190, tabs[0][1]), (190, tabs[1][0]), (188, tabs[1][0])]
    P.outline = [outer, slot]
    k = 0
    for (y0, y1) in tabs:
        for x in (188.0, 190.0):
            for i in range(5):
                k += 1
                P.parts.append(Part(f"MB{k}", "Hole_2.2", x, (y0 + y1) / 2 - 1.6 + i * 0.8, 0))
    # mouse-bite holes are 0.5 mm: use a dedicated tiny footprint
    LIB["MouseBite_0.5"] = kgen.FP("MouseBite_0.5", [kgen.Pad("", "np_thru_hole", "circle", 0, 0, 0.5, 0.5, kgen.NPTH, drill=0.5)], None, attr="exclude")
    for p in P.parts:
        if p.ref.startswith("MB"): p.fp = LIB["MouseBite_0.5"]
    d = f"{PCB}/panel"
    project_files(d, "dsky_panel", None)
    write_pcb(P, f"{d}/dsky_panel.kicad_pcb", "", "DSKY PCB panel (keyboard + status-light board)")
    return P


# ---------------------------------------------------------------- JLCPCB BOM / CPL
def jlc_files(b, d, name):
    os.makedirs(d, exist_ok=True)
    rows = {}
    with open(f"{d}/{name}_CPL.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for p in b.parts:
            if not p.lcsc or p.dnp or not p.assembled: continue
            w.writerow([p.ref, f"{p.x:.3f}mm", f"{-p.y:.3f}mm", "Top" if p.side == "F" else "Bottom", f"{p.deg % 360:.0f}"])
            key = (p.value, p.fp.name, p.lcsc)
            rows.setdefault(key, []).append(p.ref)
    with open(f"{d}/{name}_BOM.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part #"])
        for (val, fp, lcsc), refs in sorted(rows.items()):
            w.writerow([val, ",".join(sorted(refs, key=lambda r: (r[0], int(''.join(c for c in r if c.isdigit()))))), fp, lcsc])
    return rows


if __name__ == "__main__":
    sb = pickle.load(open("out/status_board.pkl", "rb"))
    kb = pickle.load(open("out/keyboard_board.pkl", "rb"))
    from keyboard_board import KEYS
    os.makedirs(f"{PCB}/lib", exist_ok=True)
    write_fp_lib(f"{PCB}/lib/dsky.pretty")
    write_sym_lib(f"{PCB}/lib/dsky.kicad_sym")
    status(sb)
    keyboard(kb, KEYS)
    P = panel(kb, sb)
    jlc_files(sb, f"{PCB}/jlcpcb/status-board", "status_board")
    jlc_files(kb, f"{PCB}/jlcpcb/keyboard-board", "keyboard_board")
    jlc_files(P, f"{PCB}/jlcpcb/panel", "dsky_panel")
    pickle.dump(P, open("out/panel.pkl", "wb"))
    errs = P.check(); con = P.connectivity()
    print("panel clearance errors:", len(errs), errs[:5])
    print("panel unconnected:", {k: v for k, v in con.items() if v != 1})
