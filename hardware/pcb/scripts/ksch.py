"""KiCad 8 schematic writer: custom 'dsky' symbols, placed parts connected by net labels on every pin."""
import uuid
U = lambda: str(uuid.uuid4())
G = 2.54


def q(s): return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
def F(v): return ("%.4f" % v).rstrip("0").rstrip(".") if abs(v) > 1e-9 else "0"


class Sym:
    """box symbol. pins: dict side -> list of (number, name) top->bottom / left->right"""
    def __init__(self, name, ref, left=(), right=(), top=(), bottom=(), w=None, desc="", body=None, value=None):
        self.name, self.ref, self.desc, self.value = name, ref, desc, value or name
        self.pins = []  # (num, name, x, y, angle)
        nl, nr = len(left), len(right)
        h = max(nl, nr, 1) * G + G
        w = w or max(4 * G, (max(len(top), len(bottom)) + 1) * G)
        self.w, self.h = w, h
        y0 = h / 2 - G
        for i, (n, s) in enumerate(left): self.pins.append((n, s, -w / 2 - G, y0 - i * G, 0))
        for i, (n, s) in enumerate(right): self.pins.append((n, s, w / 2 + G, y0 - i * G, 180))
        x0 = -(len(top) - 1) * G / 2
        for i, (n, s) in enumerate(top): self.pins.append((n, s, x0 + i * G, h / 2 + G, 270))
        x0 = -(len(bottom) - 1) * G / 2
        for i, (n, s) in enumerate(bottom): self.pins.append((n, s, x0 + i * G, -h / 2 - G, 90))
        self.body = body

    def lib(self):
        o = [f'    (symbol {q("dsky:" + self.name)} (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
             f'      (property "Reference" {q(self.ref)} (at 0 {F(self.h / 2 + 1.5)} 0) (effects (font (size 1.27 1.27))))',
             f'      (property "Value" {q(self.value)} (at 0 {F(-self.h / 2 - 1.5)} 0) (effects (font (size 1.27 1.27))))',
             '      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             '      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'      (property "Description" {q(self.desc)} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'      (symbol {q(self.name + "_0_1")}',
             f'        (rectangle (start {F(-self.w / 2)} {F(self.h / 2)}) (end {F(self.w / 2)} {F(-self.h / 2)}) (stroke (width 0.254) (type default)) (fill (type background)))',
             '      )', f'      (symbol {q(self.name + "_1_1")}']
        for n, s, x, y, a in self.pins:
            o.append(f'        (pin passive line (at {F(x)} {F(y)} {a}) (length {F(G)}) (name {q(s)} (effects (font (size 1.0 1.0)))) (number {q(n)} (effects (font (size 1.0 1.0)))))')
        o += ['      )', '    )']
        return "\n".join(o)


SYMS = {
    "WS2812B": Sym("WS2812B", "D", left=[("4", "DIN")], right=[("2", "DOUT")], top=[("1", "VDD")], bottom=[("3", "VSS")], desc="Addressable RGB LED 5050"),
    "C": Sym("C", "C", left=[("1", "1")], right=[("2", "2")], w=2 * G, desc="Capacitor"),
    "R": Sym("R", "R", left=[("1", "1")], right=[("2", "2")], w=2 * G, desc="Resistor"),
    "D": Sym("D", "D", left=[("2", "A")], right=[("1", "K")], w=2 * G, desc="Diode (pad 1 = cathode)"),
    "SW": Sym("SW", "SW", left=[("1", "1")], right=[("2", "2")], w=2 * G, desc="Key switch (Gateron LP hot-swap socket)"),
    "Conn3": Sym("Conn3", "J", left=[("1", "1"), ("2", "2"), ("3", "3")], w=2 * G, desc="3-pin connector / solder pads"),
    "74AHCT1G125": Sym("74AHCT1G125", "U", left=[("2", "A"), ("1", "~{OE}")], right=[("4", "Y")], top=[("5", "VCC")], bottom=[("3", "GND")], desc="Single buffer, 5 V output, TTL-level input"),
    "RP2040-Zero": Sym("RP2040-Zero", "U",
                       left=[("23", "5V"), ("22", "GND"), ("21", "3V3"), ("20", "GP29"), ("19", "GP28"), ("18", "GP27"), ("17", "GP26"), ("16", "GP15"), ("15", "GP14"),
                             ("14", "GP13"), ("13", "GP12"), ("12", "GP11")],
                       right=[("1", "GP0"), ("2", "GP1"), ("3", "GP2"), ("4", "GP3"), ("5", "GP4"), ("6", "GP5"), ("7", "GP6"), ("8", "GP7"), ("9", "GP8"),
                              ("10", "GP9"), ("11", "GP10")], w=8 * G, desc="Waveshare RP2040-Zero module"),
    "Hole": Sym("Hole", "H", w=2 * G, desc="Mounting / alignment hole"),
    "WS2812B_Mini": Sym("WS2812B_Mini", "LED", left=[("DI", "DIN")], right=[("DO", "DOUT")], top=[("5V", "5V")], bottom=[("G", "GND")], desc="WS2812B on a small round carrier board (wired by hand)"),
    "RPiZero": Sym("RPiZero", "U", left=[("PWR", "USB PWR (micro-USB)"), ("USB", "USB DATA (micro-USB)")], right=[("GPIO", "40-pin GPIO")], w=14 * G, desc="Raspberry Pi Zero 2 W"),
    "HyperPixel": Sym("HyperPixel", "DS", left=[("GPIO", "40-pin header")], w=12 * G, desc="Pimoroni HyperPixel 4.0 Touch"),
    "USBC_In": Sym("USBC_In", "J", right=[("V", "5V"), ("G", "GND")], w=6 * G, desc="USB-C panel-mount power input"),
}


class Placed:
    def __init__(self, sym, ref, x, y, value="", fp="", lcsc="", nets=None, mpn="", dnp=False, uuid_=None):
        self.s, self.ref, self.x, self.y = SYMS[sym], ref, x, y
        self.value, self.fp, self.lcsc, self.mpn, self.nets, self.dnp = value or SYMS[sym].value, fp, lcsc, mpn, nets or {}, dnp
        self.uuid = uuid_ or U()


def write_sch(path, project, parts, title, notes=(), rev="1.0", paper="A3", wires=()):
    root = U()
    o = [f'(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")', f'  (uuid {q(root)})', f'  (paper {q(paper)})',
         f'  (title_block (title {q(title)}) (rev {q(rev)}) (company "AGC DSKY HA terminal"))', '  (lib_symbols']
    for name in sorted({p.s.name for p in parts}): o.append(SYMS[name].lib())
    o.append('  )')
    for p in parts:
        s = p.s
        o.append(f'  (symbol (lib_id {q("dsky:" + s.name)}) (at {F(p.x)} {F(p.y)} 0) (unit 1) (exclude_from_sim no) (in_bom {"yes" if s.name != "Hole" else "no"}) (on_board yes) (dnp {"yes" if p.dnp else "no"})')
        o.append(f'    (uuid {q(p.uuid)})')
        o.append(f'    (property "Reference" {q(p.ref)} (at {F(p.x)} {F(p.y - s.h / 2 - 1.8)} 0) (effects (font (size 1.27 1.27))))')
        o.append(f'    (property "Value" {q(p.value)} (at {F(p.x)} {F(p.y + s.h / 2 + 1.8)} 0) (effects (font (size 1.27 1.27))))')
        o.append(f'    (property "Footprint" {q(p.fp)} (at {F(p.x)} {F(p.y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        o.append(f'    (property "Datasheet" "" (at {F(p.x)} {F(p.y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        if p.lcsc: o.append(f'    (property "LCSC" {q(p.lcsc)} (at {F(p.x)} {F(p.y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        if p.mpn: o.append(f'    (property "MPN" {q(p.mpn)} (at {F(p.x)} {F(p.y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        for n, *_ in s.pins: o.append(f'    (pin {q(n)} (uuid {q(U())}))')
        o.append(f'    (instances (project {q(project)} (path {q("/" + root)} (reference {q(p.ref)}) (unit 1))))')
        o.append('  )')
        for n, nm, px, py, a in s.pins:
            net = p.nets.get(n)
            if not net: continue
            x, y = p.x + px, p.y - py
            ang, just = {0: (180, "right"), 180: (0, "left"), 270: (90, "left"), 90: (270, "right")}[a]
            o.append(f'  (label {q(net)} (at {F(x)} {F(y)} {ang}) (effects (font (size 1.0 1.0)) (justify {just} bottom)) (uuid {q(U())}))')
    for (x0, y0, x1, y1) in wires:
        o.append(f'  (wire (pts (xy {F(x0)} {F(y0)}) (xy {F(x1)} {F(y1)})) (stroke (width 0) (type default)) (uuid {q(U())}))')
    for (txt, x, y, size) in notes:
        o.append(f'  (text {q(txt)} (exclude_from_sim no) (at {F(x)} {F(y)} 0) (effects (font (size {F(size)} {F(size)})) (justify left top)) (uuid {q(U())}))')
    o.append('  (sheet_instances (path "/" (page "1")))')
    o.append(')')
    open(path, "w").write("\n".join(o) + "\n")
    return root


def write_sym_lib(path):
    o = ['(kicad_symbol_lib (version 20231120) (generator "dsky_kgen") (generator_version "8.0")']
    for s in SYMS.values():
        o.append(s.lib().replace(q("dsky:" + s.name), q(s.name), 1))
    o.append(')')
    open(path, "w").write("\n".join(o) + "\n")
