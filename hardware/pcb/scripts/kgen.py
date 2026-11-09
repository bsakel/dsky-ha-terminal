"""Tiny KiCad 8 generator: footprints, PCB writer, grid autorouter, clearance/connectivity checker.
Coordinates are KiCad board coordinates (mm, y down). Footprints are defined in front view;
footprints placed on the back are mirrored in x, as KiCad does when flipping."""
import math, uuid, heapq
import numpy as np

U = lambda: str(uuid.uuid4())
F = lambda v: ("%.4f" % v).rstrip("0").rstrip(".") if abs(v) > 1e-9 else "0"

# ------------------------------------------------------------------ footprint library
class Pad:
    def __init__(self, num, kind, shape, x, y, w, h, layers, drill=None, name=""):
        self.num, self.kind, self.shape, self.x, self.y, self.w, self.h = num, kind, shape, x, y, w, h
        self.layers, self.drill, self.name = layers, drill, name


SMD_F = ["F.Cu", "F.Paste", "F.Mask"]
SMD_B = ["B.Cu", "B.Paste", "B.Mask"]
THT = ["*.Cu", "*.Mask"]
NPTH = ["*.Cu", "*.Mask"]


class FP:
    def __init__(self, name, pads, body=None, attr="smd", desc="", crtyd=None):
        self.name, self.pads, self.body, self.attr, self.desc = name, pads, body, attr, desc  # body: (x0,y0,x1,y1) courtyard + fab
        # crtyd overrides the courtyard: [("F"|"B", "rect", x0, y0, x1, y1) | ("F"|"B", "circle", r)]; body then only draws F.Fab
        self.crtyd = crtyd


def fp_lib():
    L = {}
    L["WS2812B_5050"] = FP("WS2812B_5050", [Pad("1", "smd", "rect", -2.45, -1.6, 1.5, 1.0, SMD_F, name="VDD"),
                                             Pad("2", "smd", "rect", -2.45, 1.6, 1.5, 1.0, SMD_F, name="DOUT"),
                                             Pad("3", "smd", "rect", 2.45, 1.6, 1.5, 1.0, SMD_F, name="VSS"),
                                             Pad("4", "smd", "rect", 2.45, -1.6, 1.5, 1.0, SMD_F, name="DIN")],
                           (-3.45, -2.75, 3.45, 2.75), desc="WS2812B 5050 (KiCad LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm geometry)")
    L["C_0603"] = FP("C_0603", [Pad("1", "smd", "roundrect", -0.775, 0, 0.9, 0.95, SMD_F), Pad("2", "smd", "roundrect", 0.775, 0, 0.9, 0.95, SMD_F)], (-1.48, -0.73, 1.48, 0.73))
    L["R_0603"] = FP("R_0603", [Pad("1", "smd", "roundrect", -0.825, 0, 0.8, 0.95, SMD_F), Pad("2", "smd", "roundrect", 0.825, 0, 0.8, 0.95, SMD_F)], (-1.48, -0.73, 1.48, 0.73))
    L["C_0805"] = FP("C_0805", [Pad("1", "smd", "roundrect", -0.95, 0, 1.0, 1.45, SMD_F), Pad("2", "smd", "roundrect", 0.95, 0, 1.0, 1.45, SMD_F)], (-1.7, -0.98, 1.7, 0.98))
    L["D_SOD-123"] = FP("D_SOD-123", [Pad("1", "smd", "rect", -1.65, 0, 0.9, 1.2, SMD_F, name="K"), Pad("2", "smd", "rect", 1.65, 0, 0.9, 1.2, SMD_F, name="A")], (-2.35, -1.15, 2.35, 1.15))
    L["SOT-23-5"] = FP("SOT-23-5", [Pad(str(i + 1), "smd", "roundrect", x, y, 1.325, 0.6, SMD_F) for i, (x, y) in
                                    enumerate([(-1.1375, -0.95), (-1.1375, 0), (-1.1375, 0.95), (1.1375, 0.95), (1.1375, -0.95)])], (-2.05, -1.7, 2.05, 1.7))
    L["Conn_1x03_P2.54"] = FP("Conn_1x03_P2.54", [Pad(str(i + 1), "thru_hole", "rect" if i == 0 else "circle", i * 2.54, 0, 1.7, 1.7, THT, drill=1.0) for i in range(3)],
                              (-1.3, -1.3, 6.38, 1.3), attr="through_hole", desc="3-pin 2.54 mm solder pads / pin header for the status-light cable")
    # Gateron low-profile hot-swap socket (geometry from github.com/niw gist); pads on B.Cu, switch pins through NPTH
    L["Gateron_LP_Hotswap"] = FP("Gateron_LP_Hotswap", [
        Pad("", "np_thru_hole", "circle", 0, 0, 5.1, 5.1, NPTH, drill=5.1),
        Pad("", "np_thru_hole", "circle", 2.6, 5.75, 3.0, 3.0, NPTH, drill=3.0),
        Pad("", "np_thru_hole", "circle", -4.4, 4.7, 3.0, 3.0, NPTH, drill=3.0),
        Pad("1", "smd", "rect", -8.275, 4.7, 2.55, 2.55, SMD_B),
        Pad("2", "smd", "rect", 6.475, 5.75, 2.55, 2.55, SMD_B)], (-9.6, -7.5, 7.8, 8.0),
        desc="Hot-swap socket for Gateron KS-27/KS-33 low-profile switches (hand-soldered)",
        crtyd=[("F", "rect", -7.75, -7.75, 7.75, 7.75),     # 15 x 15 switch housing
               ("B", "rect", -9.75, 2.0, 8.0, 8.3)])       # socket body and pads (from pad geometry; check datasheet)
    # Waveshare RP2040-Zero, front view, USB-C towards -y. Castellated edge pads, long enough for header pins or flat soldering.
    pads = []
    left = ["5V", "GND", "3V3", "GP29", "GP28", "GP27", "GP26", "GP15", "GP14"]       # pins 23..15 top->bottom
    right = ["GP0", "GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7", "GP8"]           # pins 1..9
    for i, n in enumerate(left):
        pads.append(Pad(str(23 - i), "smd", "rect", -8.0, -10.16 + 2.54 * i, 2.0, 1.6, SMD_F, name=n))
    for i, n in enumerate(right):
        pads.append(Pad(str(1 + i), "smd", "rect", 8.0, -10.16 + 2.54 * i, 2.0, 1.6, SMD_F, name=n))
    for i, n in enumerate(["GP9", "GP10", "GP11", "GP12", "GP13"]):                  # bottom edge, right->left
        pads.append(Pad(str(10 + i), "smd", "rect", 5.08 - 2.54 * i, 11.0, 1.6, 2.4, SMD_F, name=n))
    L["RP2040-Zero"] = FP("RP2040-Zero", pads, (-9.5, -12.25, 9.5, 12.25),
                          desc="Waveshare RP2040-Zero, soldered flat by its castellated edges (verify against your module before ordering)")
    L["MountingHole_M3"] = FP("MountingHole_M3", [Pad("", "np_thru_hole", "circle", 0, 0, 3.2, 3.2, NPTH, drill=3.2)], (-3.0, -3.0, 3.0, 3.0), attr="exclude",
                              crtyd=[("F", "circle", 3.1), ("B", "circle", 3.5)])   # M3 button head (D5.7) front, D6.5 spacer back
    L["Hole_2.2"] = FP("Hole_2.2", [Pad("", "np_thru_hole", "circle", 0, 0, 2.2, 2.2, NPTH, drill=2.2)], (-1.6, -1.6, 1.6, 1.6), attr="exclude")
    return L


LIB = fp_lib()


# ------------------------------------------------------------------ placed parts
def rot(x, y, deg):
    a = math.radians(deg); c, s = round(math.cos(a), 12), round(math.sin(a), 12)
    return x * c + y * s, -x * s + y * c          # KiCad: positive angle = counter-clockwise on screen (y down)


class Part:
    def __init__(self, ref, fp, x, y, deg=0, side="F", value="", nets=None, lcsc="", mpn="", dnp=False, assembled=True):
        self.ref, self.fp, self.x, self.y, self.deg, self.side = ref, LIB[fp], x, y, deg, side
        self.value, self.nets, self.lcsc, self.mpn, self.dnp, self.assembled = value, nets or {}, lcsc, mpn, dnp, assembled
        self.uuid, self.sym_uuid = U(), U()

    def pad_world(self, p):
        lx = -p.x if self.side == "B" else p.x
        dx, dy = rot(lx, p.y, self.deg)
        return self.x + dx, self.y + dy

    def pad_layers(self, p):
        if self.side == "B":
            sw = {"F.Cu": "B.Cu", "F.Paste": "B.Paste", "F.Mask": "B.Mask", "B.Cu": "F.Cu", "B.Paste": "F.Paste", "B.Mask": "F.Mask"}
            return [sw.get(l, l) for l in p.layers]
        return p.layers

    def pad_rect(self, p):
        """axis-aligned half sizes in world (rotation 0/90/180/270 only)"""
        w, h = (p.w, p.h) if self.deg % 180 == 0 else (p.h, p.w)
        return w / 2, h / 2


# ------------------------------------------------------------------ geometry primitives for routing / checking
class Shape:
    """copper/hole primitive: kind 'rect' (cx,cy,hw,hh) | 'circle' (cx,cy,r) | 'seg' (x0,y0,x1,y1,hw)"""
    def __init__(self, kind, layer, net, *a, src=""):
        self.kind, self.layer, self.net, self.a, self.src = kind, layer, net, a, src

    def bbox(self):
        k, a = self.kind, self.a
        if k == "rect": return a[0] - a[2], a[1] - a[3], a[0] + a[2], a[1] + a[3]
        if k == "circle": return a[0] - a[2], a[1] - a[2], a[0] + a[2], a[1] + a[2]
        return min(a[0], a[2]) - a[4], min(a[1], a[3]) - a[4], max(a[0], a[2]) + a[4], max(a[1], a[3]) + a[4]


def _seg_point_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / L2))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def _seg_seg_dist(a, b):
    def inter(p1, p2, p3, p4):
        d = lambda a, b, c: (c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])
        d1, d2, d3, d4 = d(p3, p4, p1), d(p3, p4, p2), d(p1, p2, p3), d(p1, p2, p4)
        return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))
    p1, p2, p3, p4 = (a[0], a[1]), (a[2], a[3]), (b[0], b[1]), (b[2], b[3])
    if inter(p1, p2, p3, p4): return 0.0
    return min(_seg_point_dist(*p1, *p3, *p4), _seg_point_dist(*p2, *p3, *p4), _seg_point_dist(*p3, *p1, *p2), _seg_point_dist(*p4, *p1, *p2))


def _rect_as_segs(cx, cy, hw, hh):
    # a rect is the Minkowski sum of a segment and a (zero) radius: use its 4 edges + interior test
    return [(cx - hw, cy - hh, cx + hw, cy - hh), (cx + hw, cy - hh, cx + hw, cy + hh), (cx + hw, cy + hh, cx - hw, cy + hh), (cx - hw, cy + hh, cx - hw, cy - hh)]


def dist(s, t):
    """edge-to-edge distance between two shapes (0 if overlapping)"""
    def core(sh):  # (segments, radius, rect-or-None)
        k, a = sh.kind, sh.a
        if k == "circle": return [(a[0], a[1], a[0], a[1])], a[2], None
        if k == "seg": return [(a[0], a[1], a[2], a[3])], a[4], None
        return _rect_as_segs(*a), 0.0, a
    sa, ra, Ra = core(s); sb, rb, Rb = core(t)
    inside = lambda R, x, y: R is not None and abs(x - R[0]) <= R[2] and abs(y - R[1]) <= R[3]
    for (x0, y0, x1, y1) in sb:
        if inside(Ra, x0, y0): return 0.0
    for (x0, y0, x1, y1) in sa:
        if inside(Rb, x0, y0): return 0.0
    d = min(_seg_seg_dist(p, q) for p in sa for q in sb)
    return max(0.0, d - ra - rb)


# ------------------------------------------------------------------ board model
class Board:
    def __init__(self, name, outline, rules=None):
        self.name, self.outline = name, outline          # outline: list of polygons (list of (x,y)); first = outer
        self.parts, self.segs, self.vias, self.texts, self.zones = [], [], [], [], []
        self.R = dict(clear=0.2, track=0.25, power=0.4, via_d=0.6, via_drill=0.3, edge=0.4, hole_clear=0.25)
        if rules: self.R.update(rules)
        self.keepouts = []   # (layer or '*', x0,y0,x1,y1) copper keepout rects

    def add(self, p): self.parts.append(p); return p

    def nets(self):
        s = set()
        for p in self.parts: s |= {n for n in p.nets.values() if n}
        return sorted(s)

    def pad_shapes(self):
        out = []
        for p in self.parts:
            for pd in p.fp.pads:
                x, y = p.pad_world(pd)
                net = p.nets.get(pd.num, "") if pd.num else ""
                lays = p.pad_layers(pd)
                cu = [l for l in ("F.Cu", "B.Cu") if l in lays or "*.Cu" in lays]
                if pd.kind == "np_thru_hole":
                    for l in ("F.Cu", "B.Cu"): out.append(Shape("circle", l, "#HOLE", x, y, pd.drill / 2, src=f"{p.ref} hole"))
                    continue
                hw, hh = p.pad_rect(pd)
                for l in cu:
                    if pd.shape == "circle": out.append(Shape("circle", l, net or f"#{p.ref}.{pd.num}", x, y, hw, src=f"{p.ref}.{pd.num}"))
                    else: out.append(Shape("rect", l, net or f"#{p.ref}.{pd.num}", x, y, hw, hh, src=f"{p.ref}.{pd.num}"))
        return out

    def copper_shapes(self):
        out = self.pad_shapes()
        for (x0, y0, x1, y1, w, layer, net) in self.segs: out.append(Shape("seg", layer, net, x0, y0, x1, y1, w / 2, src="track"))
        for (x, y, net) in self.vias:
            for l in ("F.Cu", "B.Cu"): out.append(Shape("circle", l, net, x, y, self.R["via_d"] / 2, src="via"))
        return out

    # ------------------------------------------------------------ checks
    def edge_segments(self):
        segs = []
        for poly in self.outline:
            for i in range(len(poly)):
                (a, b), (c, d) = poly[i], poly[(i + 1) % len(poly)]
                segs.append((a, b, c, d))
        return segs

    def check(self):
        sh = self.copper_shapes()
        errs = []
        # clearance between different nets on the same layer
        by_layer = {}
        for s in sh: by_layer.setdefault(s.layer, []).append(s)
        for layer, L in by_layer.items():
            bbs = np.array([s.bbox() for s in L])
            for i, s in enumerate(L):
                m = (bbs[:, 0] <= bbs[i, 2] + 0.5) & (bbs[:, 2] >= bbs[i, 0] - 0.5) & (bbs[:, 1] <= bbs[i, 3] + 0.5) & (bbs[:, 3] >= bbs[i, 1] - 0.5)
                for j in np.nonzero(m)[0]:
                    if j <= i: continue
                    t = L[j]
                    if s.net == t.net and not s.net.startswith("#"): continue
                    if s.net.startswith("#HOLE") and t.net.startswith("#HOLE"): continue
                    need = self.R["hole_clear"] if "#HOLE" in (s.net, t.net) else self.R["clear"]
                    if s.src == t.src and s.src.endswith("hole"): continue
                    d = dist(s, t)
                    if d < need - 1e-4:
                        errs.append((round(d, 3), layer, s.src, s.net, t.src, t.net))
        # board edge clearance
        es = [Shape("seg", "*", "#EDGE", *e, 0.0) for e in self.edge_segments()]
        for s in sh:
            if s.net == "#HOLE": continue
            for e in es:
                d = dist(s, e)
                if d < self.R["edge"] - 1e-4: errs.append((round(d, 3), s.layer, s.src, s.net, "board edge", "")); break
        return errs

    def connectivity(self):
        """for each net: number of connected copper islands (pads+tracks+vias, via joins layers)"""
        sh = [s for s in self.copper_shapes() if not s.net.startswith("#")]
        res = {}
        for net in self.nets():
            S = [s for s in sh if s.net == net]
            # THT pads (*.Cu) appear on both layers with the same src -> join them
            parent = list(range(len(S)))
            def f(i):
                while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
                return i
            for i in range(len(S)):
                for j in range(i + 1, len(S)):
                    a, b = S[i], S[j]
                    same_obj = a.src == b.src and a.src not in ("track",) and (a.a[:2] == b.a[:2])
                    if same_obj or (a.layer == b.layer and dist(a, b) <= 1e-6):
                        parent[f(i)] = f(j)
            pads = [i for i, s in enumerate(S) if s.src not in ("track", "via")]
            groups = {f(i) for i in pads}
            res[net] = len(groups)
        return res


# ------------------------------------------------------------------ grid autorouter
class Router:
    def __init__(self, board, grid=0.2, via_cost=12.0, layers=("F.Cu", "B.Cu"), allow_layers=None):
        self.b, self.g, self.via_cost = board, grid, via_cost
        self.layers = list(layers)
        xs = [x for poly in board.outline for x, _ in poly]; ys = [y for poly in board.outline for _, y in poly]
        self.x0, self.y0 = min(xs) - 1, min(ys) - 1
        self.nx, self.ny = int((max(xs) - self.x0 + 1) / grid) + 2, int((max(ys) - self.y0 + 1) / grid) + 2
        self.allow_layers = allow_layers or {}

    def cell(self, x, y): return int(round((x - self.x0) / self.g)), int(round((y - self.y0) / self.g))
    def pos(self, i, j): return self.x0 + i * self.g, self.y0 + j * self.g

    def blocked_grid(self, net, width):
        """boolean [layer, nx, ny]: True where a track centre of `width` for `net` may not go"""
        b, R = self.b, self.b.R
        G = np.zeros((len(self.layers), self.nx, self.ny), bool)
        I, J = np.meshgrid(np.arange(self.nx), np.arange(self.ny), indexing="ij")
        X, Y = self.x0 + I * self.g, self.y0 + J * self.g
        hw = width / 2
        # outside board / near edge
        from matplotlib.path import Path
        outer = Path(b.outline[0])
        ins = outer.contains_points(np.column_stack([X.ravel(), Y.ravel()])).reshape(X.shape)
        for poly in b.outline[1:]:
            ins &= ~Path(poly).contains_points(np.column_stack([X.ravel(), Y.ravel()])).reshape(X.shape)
        edge_d = np.full(X.shape, 1e9)
        for (a, c, d, e) in b.edge_segments():
            dx, dy = d - a, e - c; L2 = dx * dx + dy * dy
            t = np.clip(((X - a) * dx + (Y - c) * dy) / L2, 0, 1)
            edge_d = np.minimum(edge_d, np.hypot(X - (a + t * dx), Y - (c + t * dy)))
        base = ~ins | (edge_d < R["edge"] + hw)
        for li in range(len(self.layers)): G[li] |= base
        for s in b.copper_shapes():
            if s.net == net: continue
            if s.layer not in self.layers: continue
            li = self.layers.index(s.layer)
            need = (R["hole_clear"] if s.net == "#HOLE" else R["clear"]) + hw
            x0, y0, x1, y1 = s.bbox()
            i0, j0 = self.cell(x0 - need - self.g, y0 - need - self.g); i1, j1 = self.cell(x1 + need + self.g, y1 + need + self.g)
            i0, j0, i1, j1 = max(i0, 0), max(j0, 0), min(i1, self.nx - 1), min(j1, self.ny - 1)
            sx, sy = X[i0:i1 + 1, j0:j1 + 1], Y[i0:i1 + 1, j0:j1 + 1]
            if s.kind == "circle":
                d = np.hypot(sx - s.a[0], sy - s.a[1]) - s.a[2]
            elif s.kind == "rect":
                dx = np.maximum(np.abs(sx - s.a[0]) - s.a[2], 0); dy = np.maximum(np.abs(sy - s.a[1]) - s.a[3], 0)
                d = np.hypot(dx, dy)
            else:
                a0, b0, a1, b1, r = s.a
                ddx, ddy = a1 - a0, b1 - b0; L2 = ddx * ddx + ddy * ddy or 1e-12
                t = np.clip(((sx - a0) * ddx + (sy - b0) * ddy) / L2, 0, 1)
                d = np.hypot(sx - (a0 + t * ddx), sy - (b0 + t * ddy)) - r
            G[li, i0:i1 + 1, j0:j1 + 1] |= d < need - 1e-6
        for (layer, x0, y0, x1, y1) in b.keepouts:
            for li, l in enumerate(self.layers):
                if layer in ("*", l):
                    i0, j0 = self.cell(x0, y0); i1, j1 = self.cell(x1, y1)
                    G[li, max(i0, 0):i1 + 1, max(j0, 0):j1 + 1] = True
        for li, l in enumerate(self.layers):
            if net in self.allow_layers and l not in self.allow_layers[net]: G[li] = True
        return G

    def via_ok_grid(self, net):
        """cells where a via (both layers) fits"""
        G = self.blocked_grid(net, self.b.R["via_d"])
        return ~(G[0] | G[1])

    def route(self, net, targets, width):
        """targets: list of (x, y, [layers]) pad points; connects them all (tree). Returns list of paths."""
        G = self.blocked_grid(net, width)
        V = self.via_ok_grid(net)
        # pads of this net: make their cells free on their layers
        def free_pad(x, y, layers):
            i, j = self.cell(x, y)
            for l in layers:
                li = self.layers.index(l)
                G[li, max(i - 1, 0):i + 2, max(j - 1, 0):j + 2] = False
        for x, y, ls in targets: free_pad(x, y, ls)
        tree = set()
        x, y, ls = targets[0]; i, j = self.cell(x, y)
        for l in ls: tree.add((self.layers.index(l), i, j))
        paths = []
        rest = list(targets[1:])
        while rest:
            # pick nearest remaining target to the tree (euclid on cells)
            tc = np.array([(c[1], c[2]) for c in tree])
            def dmin(t):
                i, j = self.cell(t[0], t[1]); return np.min(np.hypot(tc[:, 0] - i, tc[:, 1] - j))
            rest.sort(key=dmin)
            tx, ty, tls = rest.pop(0)
            ti, tj = self.cell(tx, ty)
            goal = {(self.layers.index(l), ti, tj) for l in tls}
            p = self._astar(G, V, tree, goal, (ti, tj))
            if p is None: return None, (tx, ty)
            paths.append(p)
            tree |= set(p)
        return paths, None

    def _astar(self, G, V, starts, goals, gxy):
        D8 = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        h = lambda i, j: math.hypot(i - gxy[0], j - gxy[1])
        openq, came, cost = [], {}, {}
        for s in starts:
            cost[s] = 0.0; heapq.heappush(openq, (h(s[1], s[2]), 0.0, s, None))
        nL = len(self.layers)
        while openq:
            f, c, node, prevdir = heapq.heappop(openq)
            if c > cost.get(node, 1e18) + 1e-9: continue
            if node in goals:
                path = [node]
                while path[-1] in came: path.append(came[path[-1]])
                return path[::-1]
            l, i, j = node
            for di, dj, w in D8:
                ni, nj = i + di, j + dj
                if not (0 <= ni < self.nx and 0 <= nj < self.ny) or G[l, ni, nj]: continue
                if di and dj and (G[l, i + di, j] or G[l, i, j + dj]): continue
                turn = 0.0 if prevdir in (None, (di, dj)) else 0.4
                nc = c + w + turn
                nn = (l, ni, nj)
                if nc < cost.get(nn, 1e18) - 1e-9:
                    cost[nn] = nc; came[nn] = node; heapq.heappush(openq, (nc + h(ni, nj), nc, nn, (di, dj)))
            if V[i, j]:
                for nl in range(nL):
                    if nl == l or G[nl, i, j]: continue
                    nn = (nl, i, j); nc = c + self.via_cost
                    if nc < cost.get(nn, 1e18) - 1e-9:
                        cost[nn] = nc; came[nn] = node; heapq.heappush(openq, (nc + h(i, j), nc, nn, None))
        return None

    def commit(self, net, paths, width):
        """turn grid paths into merged straight segments + vias on the board"""
        for p in paths:
            run = [p[0]]
            def flush(run):
                if len(run) < 2: return
                (l, i0, j0), (_, i1, j1) = run[0], run[-1]
                x0, y0 = self.pos(i0, j0); x1, y1 = self.pos(i1, j1)
                self.b.segs.append((x0, y0, x1, y1, width, self.layers[l], net))
            for a, b in zip(p, p[1:]):
                if a[0] != b[0]:                       # via
                    flush(run); x, y = self.pos(a[1], a[2]); self.b.vias.append((x, y, net)); run = [b]; continue
                if len(run) >= 2:
                    d0 = (run[1][1] - run[0][1], run[1][2] - run[0][2]); d1 = (b[1] - a[1], b[2] - a[2])
                    if d0 != d1: flush(run); run = [a]
                run.append(b)
            flush(run)

    def stub(self, net, x, y, cx, cy, layer, width):
        """connect exact pad centre (x,y) to the snapped grid point (cx,cy)"""
        if abs(x - cx) > 1e-6 or abs(y - cy) > 1e-6:
            self.b.segs.append((x, y, cx, cy, width, layer, net))


# ------------------------------------------------------------------ KiCad writer
LAYERS = """  (layers
    (0 "F.Cu" signal) (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user) (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2") (44 "Edge.Cuts" user) (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user)
  )"""


def q(s): return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def fp_sexpr(p, netidx, sheetfile, standalone=False):
    side = p.side
    L = lambda l: (l.replace("F.", "B.") if l.startswith("F.") else l.replace("B.", "F.")) if side == "B" else l
    mir = " (justify mirror)" if side == "B" else ""
    out = []
    at = f"(at {F(p.x)} {F(p.y)}{(' ' + F(p.deg)) if p.deg else ''})" if not standalone else ""
    out.append(f'  (footprint {q("dsky:" + p.fp.name)} (layer {q(L("F.Cu"))}) (uuid {q(p.uuid)}) {at}')
    if p.fp.desc: out.append(f'    (descr {q(p.fp.desc)})')
    rx, ry = 0, (p.fp.body[1] - 1.2) if p.fp.body else -2
    out.append(f'    (property "Reference" {q(p.ref if not standalone else "REF**")} (at 0 {F(ry)} {F(p.deg)}) (layer {q(L("F.SilkS"))}) (uuid {q(U())}) (effects (font (size 0.8 0.8) (thickness 0.12)){mir}))')
    out.append(f'    (property "Value" {q(p.value or p.fp.name)} (at 0 {F((p.fp.body[3] + 1.2) if p.fp.body else 2)} {F(p.deg)}) (layer {q(L("F.Fab"))}) (uuid {q(U())}) (effects (font (size 0.8 0.8) (thickness 0.12)){mir}))')
    out.append(f'    (property "Footprint" {q("dsky:" + p.fp.name)} (at 0 0 0) (layer {q(L("F.Fab"))}) (hide yes) (uuid {q(U())}) (effects (font (size 1 1) (thickness 0.15))))')
    if p.lcsc: out.append(f'    (property "LCSC" {q(p.lcsc)} (at 0 0 0) (layer {q(L("F.Fab"))}) (hide yes) (uuid {q(U())}) (effects (font (size 1 1) (thickness 0.15))))')
    if not standalone:
        out.append(f'    (path {q("/" + p.sym_uuid)}) (sheetname "Root") (sheetfile {q(sheetfile)})')
    attr = {"smd": "(attr smd)", "through_hole": "(attr through_hole)", "exclude": "(attr exclude_from_pos_files exclude_from_bom)"}[p.fp.attr]
    if p.dnp or not p.assembled:
        attr = attr[:-1] + (" exclude_from_pos_files" if "exclude_from_pos" not in attr else "") + (" dnp" if p.dnp else "") + ")"
    out.append("    " + attr)
    if p.fp.body:
        x0, y0, x1, y1 = p.fp.body
        for (a, b, c, d) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
            a, c = (-a, -c) if side == "B" else (a, c)
            if not p.fp.crtyd:
                out.append(f'    (fp_line (start {F(a)} {F(b)}) (end {F(c)} {F(d)}) (stroke (width 0.05) (type solid)) (layer {q(L("F.CrtYd"))}) (uuid {q(U())}))')
            out.append(f'    (fp_line (start {F(a)} {F(b)}) (end {F(c)} {F(d)}) (stroke (width 0.1) (type solid)) (layer {q(L("F.Fab"))}) (uuid {q(U())}))')
    for cy in p.fp.crtyd or []:
        lay = q(L(cy[0] + ".CrtYd"))
        if cy[1] == "circle":
            out.append(f'    (fp_circle (center 0 0) (end {F(cy[2])} 0) (stroke (width 0.05) (type solid)) (fill none) (layer {lay}) (uuid {q(U())}))')
            continue
        x0, y0, x1, y1 = cy[2:]
        for (a, b, c, d) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
            a, c = (-a, -c) if side == "B" else (a, c)
            out.append(f'    (fp_line (start {F(a)} {F(b)}) (end {F(c)} {F(d)}) (stroke (width 0.05) (type solid)) (layer {lay}) (uuid {q(U())}))')
    for pd in p.fp.pads:
        lays = " ".join(q(L(l)) if not l.startswith("*") else q(l) for l in pd.layers)
        px = -pd.x if side == "B" else pd.x
        pa = f"(at {F(px)} {F(pd.y)}{(' ' + F(p.deg)) if p.deg else ''})"
        drill = f" (drill {F(pd.drill)})" if pd.drill else ""
        rr = " (roundrect_rratio 0.25)" if pd.shape == "roundrect" else ""
        net = ""
        if pd.num and not standalone and p.nets.get(pd.num):
            n = p.nets[pd.num]; net = f" (net {netidx[n]} {q(n)})"
        out.append(f'    (pad {q(pd.num)} {pd.kind} {pd.shape} {pa} (size {F(pd.w)} {F(pd.h)}){drill} (layers {lays}){rr}{net} (uuid {q(U())}))')
    out.append("  )")
    return "\n".join(out)


def write_pcb(board, path, sheetfile, title="", rev="1.0"):
    nets = [""] + board.nets()
    idx = {n: i for i, n in enumerate(nets)}
    o = ['(kicad_pcb (version 20240108) (generator "dsky_kgen") (generator_version "8.0")',
         '  (general (thickness 1.6) (legacy_teardrops no))', '  (paper "A4")',
         f'  (title_block (title {q(title)}) (rev {q(rev)}) (company "AGC DSKY HA terminal"))', LAYERS,
         '  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))']
    for n in nets: o.append(f'  (net {idx[n]} {q(n)})')
    for p in board.parts: o.append(fp_sexpr(p, idx, sheetfile))
    for poly in board.outline:
        for i in range(len(poly)):
            (a, b), (c, d) = poly[i], poly[(i + 1) % len(poly)]
            o.append(f'  (gr_line (start {F(a)} {F(b)}) (end {F(c)} {F(d)}) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid {q(U())}))')
    for (x0, y0, x1, y1, w, layer, net) in board.segs:
        o.append(f'  (segment (start {F(x0)} {F(y0)}) (end {F(x1)} {F(y1)}) (width {F(w)}) (layer {q(layer)}) (net {idx[net]}) (uuid {q(U())}))')
    for (x, y, net) in board.vias:
        o.append(f'  (via (at {F(x)} {F(y)}) (size {F(board.R["via_d"])}) (drill {F(board.R["via_drill"])}) (layers "F.Cu" "B.Cu") (net {idx[net]}) (uuid {q(U())}))')
    for (txt, x, y, layer, size, deg) in board.texts:
        mir = " (justify mirror)" if layer.startswith("B.") else ""
        o.append(f'  (gr_text {q(txt)} (at {F(x)} {F(y)} {F(deg)}) (layer {q(layer)}) (uuid {q(U())}) (effects (font (size {F(size)} {F(size)}) (thickness {F(size * 0.15)})){mir}))')
    for (net, layer, poly) in board.zones:
        pts = " ".join(f"(xy {F(x)} {F(y)})" for x, y in poly)
        o.append(f'  (zone (net {idx[net]}) (net_name {q(net)}) (layer {q(layer)}) (uuid {q(U())}) (hatch edge 0.5) (connect_pads (clearance 0.3)) (min_thickness 0.25) (filled_areas_thickness no) (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5)) (polygon (pts {pts})))')
    o.append(")")
    open(path, "w").write("\n".join(o) + "\n")


def write_fp_lib(dirpath):
    import os
    os.makedirs(dirpath, exist_ok=True)
    for name, fp in LIB.items():
        p = Part("REF**", name, 0, 0)
        s = fp_sexpr(p, {}, "", standalone=True)
        s = s.replace("  (footprint", "(footprint", 1).replace("\n    ", "\n  ")
        s = s[:-3] + ")" if s.endswith("\n  )") else s
        open(f"{dirpath}/{name}.kicad_mod", "w").write(s + "\n")
