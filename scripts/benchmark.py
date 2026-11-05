"""ArqBIM benchmark (instructions, section 6): the program's speed, measured the same way at every phase.

    .venv\\Scripts\\python scripts\\benchmark.py                   generated building, size "medio"
    .venv\\Scripts\\python scripts\\benchmark.py --tamanho grande  pequeno | medio | grande
    .venv\\Scripts\\python scripts\\benchmark.py C:\\obra\\projeto.ifc  any IFC (e.g. exported from Revit)

The generated building is made with the program's own commands (walls, doors,
windows, slabs, a group copied on a grid and repeated on every storey) and kept
in benchmark/modelos. Results go to benchmark/resultados.md (readable) and
benchmark/resultados.jsonl (one line per run, to compare phases).

What is measured (the targets of the instructions where there is one):
  - open: reading the IFC; open in the program up to the first image   (500 MB < 20 s)
    the first time (shapes worked out) and again (shapes from the geometry cache)
  - navigation: images per second while orbiting                       (60 fps)
  - regenerate one changed wall, up to the new image                    (< 50 ms)
  - select with the mouse (GPU pick)                                    (< 16 ms)
  - inferences (snap) under the cursor, save, memory.
"""

import argparse
import ctypes
import datetime
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from arqbim import __version__  # noqa: E402
from arqbim.core.transform import translation  # noqa: E402
from arqbim.core.walls import find_joint  # noqa: E402
from arqbim.ifc import catalog  # noqa: E402
from arqbim.model import bim, geomcache  # noqa: E402
from arqbim.model.document import Document, read_file, read_preview  # noqa: E402

OUT = os.path.join(ROOT, "benchmark")
MODELS = os.path.join(OUT, "modelos")
SIZES = {"pequeno": (3, 3, 3), "medio": (6, 6, 5), "grande": (10, 10, 10)}   # apartments x, y, storeys
FLAT = (8.0, 6.0)                 # one apartment, axis to axis
STEP = (9.0, 7.0)                 # grid spacing
STOREY_HEIGHT = 3.0
TARGETS = {"open_500mb_s": 20.0, "fps": 60.0, "regen_ms": 50.0, "pick_ms": 16.0,
           "snap_ms": 16.0}   # a mouse move answered within one 60 Hz frame (our target, like selecting)


def now():
    return time.perf_counter()


def memory_mb():
    """Peak memory of this process (Windows; on Linux — WSL — its peak resident size, 0.283), or None."""
    if sys.platform.startswith("linux"):
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    try:
        class Counters(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        c = Counters()
        c.cb = ctypes.sizeof(c)
        kernel32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p          # a 64-bit handle, not an int
        psapi.GetProcessMemoryInfo.argtypes = (ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong)
        if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb):
            return None
        return c.PeakWorkingSetSize / 1e6
    except Exception:
        return None


# ---------------------------------------------------------------- the generated building

def apartment(doc):
    """One apartment drawn with the program's commands; returns its elements."""
    wall20, wall15 = catalog.BY_KEY["parede_alv_20"], catalog.BY_KEY["parede_alv_15"]
    w, h = FLAT
    pts = [np.array(p, float) for p in ((0, 0, 0), (w, 0, 0), (w, h, 0), (0, h, 0))]
    walls, prev, first = [], None, None
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        d = (b - a) / np.linalg.norm(b - a)
        g = bim.add_wall(doc, a, b, wall20, prev=prev, first=first if i == 3 else None)
        walls.append(g)
        prev = (g, d)
        if i == 0:
            first = (g, d)
    # an inner wall across the flat (a T junction at each end)
    a, b = np.array((w / 2, 0, 0)), np.array((w / 2, h, 0))
    d = (b - a) / np.linalg.norm(b - a)
    axes = bim.wall_axes(doc)
    sj, ej = find_joint(a, d, axes, 0.15), find_joint(b, d, axes, 0.15)
    walls.append(bim.add_wall(doc, a, b, wall15, start_join=sj and sj[:3], end_join=ej and ej[:3]))
    door, door2, window = (catalog.OPENING_BY_KEY[k] for k in ("porta_90", "porta_80", "janela_120"))
    bim.add_opening(doc, walls[0], door, bim.wall_frame(doc, walls[0]), 1.0, -1)
    bim.add_opening(doc, walls[4], door2, bim.wall_frame(doc, walls[4]), 2.5, -1)
    for wall, s in ((walls[1], 2.0), (walls[2], 1.5), (walls[2], 5.5), (walls[3], 2.5)):
        bim.add_opening(doc, wall, window, bim.wall_frame(doc, wall), s, -1)
    bim.add_slab(doc, np.array((-0.1, -0.1, 0.0)), w + 0.2, h + 0.2, catalog.BY_KEY["laje_12"])
    return [o.id for o in doc.objects.values() if o.is_bim]


def generate(path, nx, ny, storeys):
    t0 = now()
    doc = Document()
    members = apartment(doc)
    bim.make_group(doc, members, "Apartamento")
    grid = [translation((i * STEP[0], j * STEP[1], 0.0)) for i in range(nx) for j in range(ny) if (i, j) != (0, 0)]
    if grid:
        bim.copy_objects(doc, members, grid, "Copiar")
    ground = [o.id for o in doc.objects.values() if o.is_bim]
    levels = [bim.add_storey(doc, "Piso {}".format(k), k * STOREY_HEIGHT) for k in range(1, storeys)]
    if levels:
        bim.repeat_on_storeys(doc, ground, levels)
    # a wall on its own (not in a group), the one whose regeneration is measured
    bim.add_wall(doc, (-5.0, 0.0, 0.0), (-5.0, 10.0, 0.0), catalog.BY_KEY["parede_alv_20"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.save(path)
    return now() - t0


# ---------------------------------------------------------------- measuring

def stats(times):
    times = sorted(times)
    return float(np.mean(times)), float(times[int(0.95 * (len(times) - 1))])


def measure(path, frames=60):
    import ifcopenshell
    from rendercanvas.offscreen import RenderCanvas
    from arqbim.render.viewport import Viewport

    r = {"file": os.path.basename(path), "size_mb": os.path.getsize(path) / 1e6}
    t = now()
    f = ifcopenshell.open(path)
    r["read_s"] = now() - t
    r["elements"] = len(f.by_type("IfcElement"))
    del f

    canvas = RenderCanvas(size=(1280, 720))
    doc = Document()
    vp = Viewport(canvas, doc)
    start_up(vp, canvas)
    geomcache.forget(path)                           # the first opening: no shapes kept from before
    r["open_s"], r["open_ready_s"], r["open_pause_ms"] = open_like_window(doc, vp, canvas, path)
    # (0.320) the seams between elements of one material, taken out a few after each image once it is open
    r["seams_s"], r["seams_frame_ms"] = settle(vp, canvas)
    r["triangles"] = int(sum(len(o.mesh.faces) for o in doc.objects.values() if o.is_bim))
    t = now()
    doc.ifc.triangulate()
    r["triangulate_s"] = now() - t
    t = now()
    doc._save_geometry(path)
    r["cache_write_s"] = now() - t
    r["cache_mb"] = os.path.getsize(geomcache.cache_path(path)) / 1e6
    r.update(reopen_in_new_process(path))           # opening again: the shapes come from the cache

    settle(vp, canvas)                               # (anything still being done after the images: done first)
    # navigation: orbit around the middle of the model — (0.344) after a few images: the laptop's GPU slows its clock
    # when idle (the reopening, in another process, left it so), its first 2–3 images ~40 ms whatever is drawn
    center, _radius = vp.scene_bounds()
    for _ in range(5):
        vp.orbit(6, 0, center)
        canvas.draw()
    times = []
    for _ in range(frames):
        vp.orbit(6, 0, center)
        t = now()
        canvas.draw()
        times.append(now() - t)
    mean, p95 = stats(times)
    r["frame_ms"], r["frame_p95_ms"], r["fps"] = mean * 1000, p95 * 1000, 1.0 / mean

    # selecting: pick the element in the middle of the image
    w, h = canvas.get_logical_size()
    times = []
    for k in range(20):
        t = now()
        vp.pick(w / 2 + k, h / 2)
        times.append(now() - t)
    r["pick_ms"] = stats(times)[0] * 1000

    # inferences: the first time (candidates prepared), then one mouse move, across the image
    t = now()
    vp.snap(w / 2, h / 2)
    r["snap_build_ms"] = (now() - t) * 1000
    times = []
    for k in range(40):
        t = now()
        vp.snap(w * (0.2 + 0.6 * (k % 8) / 7), h * (0.3 + 0.4 * (k // 8) / 4))
        times.append(now() - t)
    r["snap_ms"] = stats(times)[0] * 1000

    # regenerating one changed wall (an editable wall not in a group), up to the new image
    single = [o.id for o in doc.objects.values() if o.is_bim and doc.ifc.kind_of(o.id) == "wall"
              and doc.ifc.group_of(o.id) is None]
    if single:
        times = []
        for k in range(8):                           # the first one prepares things once: not counted
            # an image just before, as when the mouse moves to the wall (the laptop's GPU slows its
            # clock after a moment idle: its first images then take ~40 ms instead of ~14 ms)
            canvas.draw()
            t = now()
            bim.resize_wall(doc, single[0], height=2.8 + 0.05 * (k + 1))
            canvas.draw()
            times.append(now() - t)
        r["regen_ms"] = float(np.median(times[1:])) * 1000
        t = now()
        vp.snap(w / 2, h / 2)                        # the first mouse move after a change
        r["snap_after_edit_ms"] = (now() - t) * 1000
    grouped = [o.id for o in doc.objects.values() if o.is_bim and doc.ifc.kind_of(o.id) == "wall"
               and doc.ifc.group_of(o.id) is not None]
    if grouped:
        r["group_copies"] = 1 + len(doc.ifc.counterparts(grouped[0]))
        t = now()
        bim.resize_wall(doc, grouped[0], height=3.0)
        canvas.draw()
        r["group_edit_ms"] = (now() - t) * 1000

    with tempfile.TemporaryDirectory() as tmp:
        copy = os.path.join(tmp, "copia.ifc")
        t = now()
        doc.save(copy)                               # IFC + shapes kept for next time
        r["save_s"] = now() - t
        geomcache.forget(copy)
    r["memory_mb"] = memory_mb()
    r["open_500mb_s"] = r["open_s"] / max(r["size_mb"], 1e-9) * 500      # straight-line estimate
    r["reopen_500mb_s"] = r["reopen_s"] / max(r["size_mb"], 1e-9) * 500
    return r


def start_up(vp, canvas):
    """What the window does when the program starts, before a file is chosen: the first image
    (empty) with the GPU programs of the batches made in advance (Viewport.warm_up)."""
    vp.warm_up()
    canvas.draw()


def settle(vp, canvas):
    """(0.320) Images drawn until what the view does a little after each one is done (the seams between elements of
    one material, after a file is opened): (seconds, the longest image in ms)."""
    t = now()
    frames = []
    while vp._seam_queue or vp._seam_again or vp._after_draw or vp.bim.pending():
        t1 = now()
        canvas.draw()
        frames.append(now() - t1)
        if now() - t > 300.0:
            break
    return now() - t, (max(frames) * 1000 if frames else 0.0)


def open_like_window(doc, vp, canvas, path):
    """Open a file as the window does: in a worker thread the kept shapes (if any, shown at once)
    and then the IFC, the other shapes and the display pieces; putting them in place and drawing
    in this thread (the window's). Returns (seconds to the first image, seconds until it can be
    edited, longest pause of this thread in ms — how long the window would not answer)."""
    import queue
    from arqbim.render.viewport import prepare_pieces
    box, chunks, sent = {}, queue.SimpleQueue(), {}
    window_free = threading.Event()                  # as the window: the reader waits while it is busy
    window_free.set()

    def check():
        window_free.wait(1.0)
        return False

    def started(preview):
        box["preview_pieces"] = prepare_pieces(preview.meshes, preview.info["classes"])
        sent.update(preview.meshes)
        box["preview"] = preview                     # (last: the window's thread looks for it)

    def partial(meshes):
        chunks.put((meshes, prepare_pieces(meshes, box["preview"].info["classes"], pause=check)))
        sent.update(meshes)

    def work():
        preview = read_preview(path)
        if preview is not None:
            started(preview)
        opened = read_file(path, cancelled=check, preview=preview, started=None if preview else started,
                           partial=partial)
        box["pieces"] = prepare_pieces({g: m for g, m in opened.shapes.items() if sent.get(g) is not m},
                                       {e.GlobalId: e.is_a() for e in opened.elements})
        box["opened"] = opened

    def draw():
        t1 = now()
        canvas.draw()
        pauses.append(now() - t1)

    t = now()
    worker = threading.Thread(target=work)
    worker.start()
    ticks, pauses, first_image, previewed = [now()], [], None, False
    while worker.is_alive() or not chunks.empty():   # the window's event loop, answering every 5 ms
        if not previewed and "preview" in box:
            window_free.clear()
            t0 = now()
            vp.adopt_pieces(box["preview_pieces"])
            doc.show_preview(box["preview"])
            vp.adopt_pieces({})
            vp.set_view("iso")
            pauses.append(now() - t0)
            draw()
            if not vp.bim.pending():                 # (0.328: as the window, the reader waits until all is drawn)
                window_free.set()
            previewed = True
            if any(o.is_bim for o in doc.objects.values()):
                first_image = now() - t
        elif previewed and not chunks.empty():
            window_free.clear()
            t0 = now()
            while not chunks.empty():
                meshes, pieces = chunks.get()
                vp.adopt_pieces(pieces)
                doc.add_preview_shapes(meshes)
                vp.adopt_pieces({})
            if first_image is None:
                vp.set_view("iso")
            pauses.append(now() - t0)
            draw()
            if not vp.bim.pending():
                window_free.set()
            if first_image is None:
                first_image = now() - t
        elif vp.bim.pending():                       # (0.328: as the window, the other batches at the next images…
            draw()
            if not vp.bim.pending():                 # …the reader waiting until all are drawn)
                window_free.set()
        else:
            time.sleep(0.005)
        ticks.append(now())
    if "opened" not in box:
        raise RuntimeError("abrir falhou: " + path)
    t0 = now()
    vp.adopt_pieces(box["pieces"])
    if previewed:
        doc.finish_opening(box["opened"])
    else:
        doc.show_file(box["opened"])
    vp.set_view("iso")
    vp.adopt_pieces({})
    t1 = now()
    canvas.draw()
    t2 = now()
    pauses += [t1 - t0, t2 - t1]
    while vp.bim.pending():                          # (0.328) ready: every batch drawn, a few per image
        t3 = now()
        canvas.draw()
        pauses.append(now() - t3)
    t2 = now()
    gaps = [b - a for a, b in zip(ticks, ticks[1:])]
    return (first_image if first_image is not None else t2 - t), t2 - t, max(gaps + pauses) * 1000


def open_once(path):
    """Open a file, as the program does (shapes from the cache if there is one)."""
    from rendercanvas.offscreen import RenderCanvas
    from arqbim.render.viewport import Viewport
    canvas = RenderCanvas(size=(1280, 720))
    doc = Document()
    vp = Viewport(canvas, doc)
    start_up(vp, canvas)
    first, ready, pause_ms = open_like_window(doc, vp, canvas, path)
    return {"reopen_s": first, "reopen_ready_s": ready, "reopen_pause_ms": pause_ms, "cache_hits": doc.cache_hits,
            "reopen_memory_mb": memory_mb()}


def reopen_in_new_process(path):
    """Reopening measured in a fresh process, like starting the program again (GPU set-up included,
    as in the first opening), not in this one where everything is already warm."""
    out = subprocess.run([sys.executable, "-W", "ignore", os.path.abspath(__file__), "--so-abrir", path],
                         capture_output=True, text=True, encoding="utf-8")
    for line in reversed(out.stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError("reabrir falhou:\n" + out.stdout + out.stderr)


def gpu_name():
    try:
        import wgpu
        info = wgpu.gpu.request_adapter_sync(power_preference="high-performance").info
        return "{} ({})".format(info.get("device", "?"), info.get("backend_type", "?"))
    except Exception:
        return "?"


# ---------------------------------------------------------------- report

def verdict(value, target, lower_is_better=True):
    if value is None:
        return "—"
    return "✔" if (value <= target if lower_is_better else value >= target) else "✘"


def report(r, generation_s=None):
    os.makedirs(OUT, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    row = dict(r, date=stamp, version=__version__, gpu=gpu_name(), generation_s=generation_s)
    with open(os.path.join(OUT, "resultados.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def n(v, fmt="{:.1f}"):
        return "—" if v is None else fmt.format(v).replace(".", ",")

    lines = [
        "## {} — ArqBIM {} — {}".format(stamp, __version__, r["file"]),
        "",
        "Modelo: {} MB, {} elementos, {} triângulos. Placa gráfica: {}.".format(
            n(r["size_mb"]), r["elements"], r["triangles"], row["gpu"])
        + ("" if generation_s is None else " Gerado pelo próprio programa em {} s.".format(n(generation_s))),
        "",
        "| Medida | Meta | Resultado | |",
        "|---|---|---|---|",
        "| Ler o IFC (IfcOpenShell) | — | {} s | |".format(n(r["read_s"], "{:.2f}")),
        "| Abrir pela 1.ª vez até à 1.ª imagem (os primeiros elementos calculados) | — | {} s | |".format(
            n(r["open_s"], "{:.2f}")),
        "| … estimativa para 500 MB (proporcional) | < 20 s | {} s | {} |".format(
            n(r["open_500mb_s"], "{:.0f}"), verdict(r["open_500mb_s"], TARGETS["open_500mb_s"])),
        "| Abrir pela 1.ª vez até tudo calculado e pronto a editar | — | {} s | |".format(
            n(r.get("open_ready_s"), "{:.2f}")),
        "| Reabrir até à 1.ª imagem, programa aberto de novo (formas guardadas, {} elementos) | — | {} s | |".format(
            r["cache_hits"], n(r["reopen_s"], "{:.2f}")),
        "| … estimativa para 500 MB (proporcional) | < 20 s | {} s | {} |".format(
            n(r["reopen_500mb_s"], "{:.0f}"), verdict(r["reopen_500mb_s"], TARGETS["open_500mb_s"])),
        "| Reabrir até poder editar (o IFC lido por trás) | — | {} s | |".format(n(r.get("reopen_ready_s"), "{:.2f}")),
        "| Janela parada ao abrir (maior pausa): 1.ª vez / reabrir | — | {} / {} ms | |".format(
            n(r["open_pause_ms"], "{:.0f}"), n(r["reopen_pause_ms"], "{:.0f}")),
        "| Tirar as juntas pelo material depois de abrir (aos poucos; a maior imagem) | — | {} s ({} ms) | |".format(
            n(r.get("seams_s"), "{:.2f}"), n(r.get("seams_frame_ms"), "{:.0f}")),
        "| Triangular todos os elementos (todos os núcleos) | — | {} s | |".format(n(r["triangulate_s"], "{:.2f}")),
        "| Guardar as formas (cache: {} MB) | — | {} s | |".format(n(r["cache_mb"]), n(r["cache_write_s"], "{:.2f}")),
        "| Navegação (orbitar): imagens por segundo | 60 fps | {} fps ({} ms; 95 % < {} ms) | {} |".format(
            n(r["fps"], "{:.0f}"), n(r["frame_ms"]), n(r["frame_p95_ms"]),
            verdict(r["fps"], TARGETS["fps"], lower_is_better=False)),
        "| Regenerar uma parede alterada (até à imagem) | < 50 ms | {} ms | {} |".format(
            n(r.get("regen_ms"), "{:.0f}"), verdict(r.get("regen_ms"), TARGETS["regen_ms"])),
        "| Selecionar com o rato (GPU) | < 16 ms | {} ms | {} |".format(
            n(r["pick_ms"]), verdict(r["pick_ms"], TARGETS["pick_ms"])),
        "| Inferências: 1.º movimento do rato (prepara os candidatos) | — | {} ms | |".format(
            n(r["snap_build_ms"], "{:.0f}")),
        "| Inferências: um movimento do rato | < 16 ms | {} ms | {} |".format(
            n(r["snap_ms"]), verdict(r["snap_ms"], TARGETS["snap_ms"])),
        "| Inferências: 1.º movimento depois de uma alteração | < 16 ms | {} ms | {} |".format(
            n(r.get("snap_after_edit_ms")), verdict(r.get("snap_after_edit_ms"), TARGETS["snap_ms"])),
    ]
    if r.get("group_edit_ms") is not None:
        lines.append("| Mudar uma parede de um grupo com {} cópias | — | {} ms | |".format(
            r["group_copies"], n(r["group_edit_ms"], "{:.0f}")))
    lines += [
        "| Gravar o IFC | — | {} s | |".format(n(r["save_s"], "{:.2f}")),
        "| Memória (pico) | — | {} MB | |".format(n(r["memory_mb"], "{:.0f}")),
        "",
    ]
    path = os.path.join(OUT, "resultados.md")
    header = "" if os.path.exists(path) else (
        "# Benchmark do ArqBIM\n\nMetas das instruções (secção 6): abrir um IFC de 500 MB < 20 s; navegação a 60 fps; "
        "regenerar uma parede < 50 ms; selecionar < 16 ms. Cada execução de `scripts/benchmark.py` acrescenta "
        "uma secção abaixo (a mais recente no fim).\n\n")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(header + "\n".join(lines) + "\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="ArqBIM benchmark")
    parser.add_argument("ifc", nargs="?", help="an IFC file to measure (default: the generated building)")
    parser.add_argument("--tamanho", choices=sorted(SIZES), default="medio")
    parser.add_argument("--regenerar", action="store_true", help="generate the building again")
    parser.add_argument("--so-abrir", action="store_true", help=argparse.SUPPRESS)   # used by reopen_in_new_process
    args = parser.parse_args()
    if args.so_abrir:
        print(json.dumps(open_once(args.ifc)), flush=True)
        return
    generation_s = None
    if args.ifc:
        path = os.path.abspath(args.ifc)
    else:
        nx, ny, storeys = SIZES[args.tamanho]
        path = os.path.join(MODELS, "edificio_{}.ifc".format(args.tamanho))
        if args.regenerar or not os.path.exists(path):
            print("A gerar o edifício '{}' ({} × {} apartamentos, {} pisos)…".format(args.tamanho, nx, ny, storeys),
                  flush=True)
            generation_s = generate(path, nx, ny, storeys)
    print("A medir {} …".format(path), flush=True)
    text = report(measure(path), generation_s)
    print(text)
    print("\nResultados em {}".format(os.path.join(OUT, "resultados.md")))


if __name__ == "__main__":
    main()
