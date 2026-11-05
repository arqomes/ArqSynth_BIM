"""The geometry engine in this process or in another one (0.283: measured before choosing, as the owner asked).

    python scripts/geometry_process.py benchmark/modelos/edificio_grande.ifc

Opens an IFC as the program does — the IFC read for editing in this process — and works out every element's
shape with IfcOpenShell's iterator, two ways:

  here     the iterator in this process, on all cores (as the program does now);
  apart    the iterator in a process of its own, which reads the IFC itself and sends the shapes back in chunks
           (numpy arrays through a pipe), while this one reads the IFC for editing.

For each: seconds until every shape is here, the longest pause of this process's main thread (a ticker every
5 ms — how long the window would not answer; the iterator's next() keeps Python's lock while it waits), and the
peak memory of this process and of the other one (Linux: peak resident size). One line of JSON each, then a
table."""

import json
import multiprocessing as mp
import os
import resource
import sys
import threading
import time

import numpy as np


def _settings():
    import ifcopenshell.geom
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    s.set("weld-vertices", True)
    return s


def _elements(f):
    return [e for e in f.by_type("IfcElement") if e.Representation is not None and not e.is_a("IfcOpeningElement")]


def _peak_mb(who=resource.RUSAGE_SELF):
    return resource.getrusage(who).ru_maxrss / 1024.0


class Ticker:
    """The window's event loop: a thread that wants to run every 5 ms; the longest gap it saw."""

    def __init__(self):
        self.gaps, self.stop = [], False
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        last = time.perf_counter()
        while not self.stop:
            time.sleep(0.005)
            now = time.perf_counter()
            self.gaps.append(now - last)
            last = now

    def longest_ms(self):
        return 1000 * max(self.gaps or [0.0])


def here(path):
    import ifcopenshell
    import ifcopenshell.geom
    ticker = Ticker()
    ticker.thread.start()
    t = time.perf_counter()
    f = ifcopenshell.open(path)
    read = time.perf_counter() - t
    out = {}
    it = ifcopenshell.geom.iterator(_settings(), f, max(1, os.cpu_count() or 1), include=_elements(f))
    if it.initialize():
        while True:
            shape = it.get()
            out[shape.guid] = (np.array(shape.geometry.verts, dtype=float).reshape(-1, 3),
                               np.array(shape.geometry.faces, dtype=np.int64).reshape(-1, 3))
            if not it.next():
                break
    total = time.perf_counter() - t
    ticker.stop = True
    return {"way": "here", "read_s": read, "shapes_s": total, "shapes": len(out),
            "pause_ms": ticker.longest_ms(), "memory_mb": _peak_mb(), "other_mb": 0.0}


def _worker(path, conn, chunk=400):
    import ifcopenshell
    import ifcopenshell.geom
    f = ifcopenshell.open(path)
    it = ifcopenshell.geom.iterator(_settings(), f, max(1, (os.cpu_count() or 2) - 1), include=_elements(f))
    batch = []
    if it.initialize():
        while True:
            shape = it.get()
            batch.append((shape.guid, np.array(shape.geometry.verts, dtype=np.float64),
                          np.array(shape.geometry.faces, dtype=np.int32)))
            if len(batch) >= chunk:
                conn.send(batch)
                batch = []
            if not it.next():
                break
    if batch:
        conn.send(batch)
    conn.send(None)
    conn.send(_peak_mb())
    conn.close()


def apart(path):
    import ifcopenshell
    ctx = mp.get_context("spawn")
    ticker = Ticker()
    ticker.thread.start()
    t = time.perf_counter()
    mine, theirs = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_worker, args=(path, theirs))
    proc.start()
    theirs.close()
    f = ifcopenshell.open(path)                    # (this process reads it too: for editing)
    read = time.perf_counter() - t
    out = {}

    def receive():
        while True:
            batch = mine.recv()
            if batch is None:
                break
            for guid, verts, faces in batch:
                out[guid] = (verts.reshape(-1, 3), faces.reshape(-1, 3).astype(np.int64))
        box["other"] = mine.recv()

    box = {}
    reader = threading.Thread(target=receive)
    reader.start()
    reader.join()
    proc.join()
    total = time.perf_counter() - t
    ticker.stop = True
    del f
    return {"way": "apart", "read_s": read, "shapes_s": total, "shapes": len(out),
            "pause_ms": ticker.longest_ms(), "memory_mb": _peak_mb(), "other_mb": box.get("other", 0.0)}


def main():
    path = sys.argv[1]
    way = sys.argv[2] if len(sys.argv) > 2 else None
    if way:                                          # (each way in a fresh process: memory peaks apart)
        print(json.dumps(dict((here if way == "here" else apart)(path), size_mb=os.path.getsize(path) / 1e6)))
        return
    import subprocess
    rows = []
    for w in ("here", "apart"):
        run = subprocess.run([sys.executable, "-W", "ignore", os.path.abspath(__file__), path, w],
                             capture_output=True, text=True)
        line = [x for x in run.stdout.splitlines() if x.startswith("{")]
        if not line:
            print(run.stdout, run.stderr)
            continue
        rows.append(json.loads(line[-1]))
        print(line[-1], flush=True)
    print("\n| | ler o IFC | todas as formas | maior pausa da janela | memória (este) | memória (o outro) |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print("| {way} | {read_s:.1f} s | {shapes_s:.1f} s ({shapes}) | {pause_ms:.0f} ms | {memory_mb:.0f} MB | "
              "{other_mb:.0f} MB |".format(**r))


if __name__ == "__main__":
    main()
