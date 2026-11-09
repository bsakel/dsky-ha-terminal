import sys, pickle; sys.path.insert(0, '.')
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon


def plot(b, out, title="", w=10):
    xs = [x for poly in b.outline for x, _ in poly]; ys = [y for poly in b.outline for _, y in poly]
    W, H = max(xs) - min(xs), max(ys) - min(ys)
    fig, ax = plt.subplots(figsize=(w, w * H / W + 0.6))
    ax.set_facecolor("#0b3d1e")
    for poly in b.outline: ax.add_patch(Polygon(poly, closed=True, fill=True, fc="#14532d", ec="#facc15", lw=1.2))
    col = {"F.Cu": "#ef4444", "B.Cu": "#3b82f6"}
    for (x0, y0, x1, y1, wd, layer, net) in sorted(b.segs, key=lambda s: s[5] == "F.Cu"):
        ax.plot([x0, x1], [y0, y1], color=col[layer], lw=wd * 72 / 25.4 * (w * 25.4 / W) / 25.4 * 2.2, solid_capstyle="round", alpha=0.9)
    for s in b.pad_shapes():
        if s.net == "#HOLE":
            ax.add_patch(Circle(s.a[:2], s.a[2], fc="black", ec="#999", lw=0.5)); continue
        c = "#fbbf24" if s.layer == "F.Cu" else "#93c5fd"
        if s.kind == "rect": ax.add_patch(Rectangle((s.a[0] - s.a[2], s.a[1] - s.a[3]), 2 * s.a[2], 2 * s.a[3], fc=c, ec="none", alpha=0.85))
        else: ax.add_patch(Circle(s.a[:2], s.a[2], fc=c, ec="none", alpha=0.85))
    for (x, y, net) in b.vias: ax.add_patch(Circle((x, y), b.R["via_d"] / 2, fc="#e5e7eb", ec="#111", lw=0.4))
    for p in b.parts:
        ax.text(p.x, p.y, p.ref, fontsize=5, color="white", ha="center", va="center", alpha=0.8)
    for (t, x, y, layer, size, deg) in b.texts:
        ax.text(x, y, t, fontsize=size * 4, color="white" if layer.startswith("F") else "#a5b4fc", ha="center", va="center", alpha=0.7)
    ax.set_xlim(min(xs) - 2, max(xs) + 2); ax.set_ylim(max(ys) + 2, min(ys) - 2); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title + "   (red = front copper, blue = back copper)", fontsize=9)
    plt.tight_layout(); plt.savefig(out, dpi=170); plt.close()


if __name__ == "__main__":
    b = pickle.load(open(sys.argv[1], "rb")); plot(b, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
