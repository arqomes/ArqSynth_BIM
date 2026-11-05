"""Point clouds read (0.161, Phase 8, step 2): a laser scan or a photogrammetry's points — XYZ / PTS / TXT (text:
x y z, and maybe an intensity and r g b), PLY (text or binary) and LAS (1.0 to 1.4, its point formats 0 to 10) —
as (N, 3) points in metres and, when the file has them, (N, 3) colours 0…1. Pure numpy. (0.284, the owner's
go-ahead to bring libraries in) LAZ — compressed LAS — through laspy with its lazrs back end, and E57 — a scanner's
XML and binary — through pye57: both open source, read only if installed (ValueError("laz") / ("e57") otherwise)."""

import os
import struct

import numpy as np

EXTENSIONS = ("xyz", "pts", "txt", "csv", "ply", "las", "laz", "e57")
LAS_RGB = {2: 20, 3: 28, 5: 28, 7: 30, 8: 30, 10: 30}      # point format -> where its red is in a record


class PointCloud:
    def __init__(self, points, colours=None):
        self.points = np.asarray(points, dtype=np.float64).reshape(-1, 3)
        self.colours = None if colours is None else np.asarray(colours, dtype=np.float32).reshape(-1, 3)

    def __len__(self):
        return len(self.points)

    def bounds(self):
        if not len(self.points):
            return None
        return self.points.min(axis=0), self.points.max(axis=0)

    def thinned(self, most, seed=0):
        """At most `most` of its points, taken evenly at random (the same ones each time)."""
        if len(self.points) <= most:
            return self
        keep = np.sort(np.random.default_rng(seed).choice(len(self.points), most, replace=False))
        return PointCloud(self.points[keep], None if self.colours is None else self.colours[keep])


def read_text(text):
    """x y z [i] [r g b] a line (spaces, tabs, commas or ";"); a first line with one number (PTS: how many) or a
    header line of words is left out."""
    lines = text.splitlines()
    start = 0
    while start < len(lines):
        tokens = lines[start].replace(",", " ").replace(";", " ").split()
        try:
            values = [float(v) for v in tokens]
        except ValueError:
            start += 1
            continue
        if len(values) >= 3:
            break
        start += 1
    if start >= len(lines):
        return PointCloud(np.zeros((0, 3)))
    columns = len(lines[start].replace(",", " ").replace(";", " ").split())
    body = "\n".join(lines[start:]).replace(",", " ").replace(";", " ")
    flat = np.array(body.split(), dtype=float)
    rows = len(flat) // columns
    data = flat[:rows * columns].reshape(rows, columns)
    colours = None
    if columns >= 6:
        rgb = data[:, columns - 3:]
        if rgb.max() > 1.0:
            rgb = rgb / (65535.0 if rgb.max() > 255 else 255.0)
        colours = rgb
    return PointCloud(data[:, :3], colours)


_PLY_TYPES = {"char": "i1", "int8": "i1", "uchar": "u1", "uint8": "u1", "short": "i2", "int16": "i2",
              "ushort": "u2", "uint16": "u2", "int": "i4", "int32": "i4", "uint": "u4", "uint32": "u4",
              "float": "f4", "float32": "f4", "double": "f8", "float64": "f8"}


def read_ply(data):
    """A PLY's vertices (its first element; text or binary, either byte order) and their colours."""
    end = data.find(b"end_header")
    if not data.startswith(b"ply") or end < 0:
        raise ValueError("not a PLY")
    header = data[:end].decode("ascii", errors="replace").splitlines()
    body = data[data.index(b"\n", end) + 1:]
    fmt, count, props, in_vertex, first = "ascii", 0, [], False, None
    for line in header:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "format":
            fmt = parts[1]
        elif parts[0] == "element":
            in_vertex = parts[1] == "vertex"
            if first is None:
                first = parts[1]
            if in_vertex:
                count = int(parts[2])
        elif parts[0] == "property" and in_vertex:
            if parts[1] == "list":
                raise ValueError("a list in the vertices")
            props.append((parts[2], _PLY_TYPES[parts[1]]))
    if first != "vertex":
        raise ValueError("the vertices are not first")
    names = [n for n, _t in props]
    if fmt == "ascii":
        rows = body.decode("ascii", errors="replace").split("\n")[:count]
        arr = np.array(" ".join(rows).split(), dtype=float).reshape(count, len(props))
        col = {n: arr[:, k] for k, n in enumerate(names)}
    else:
        order = "<" if fmt == "binary_little_endian" else ">"
        dtype = np.dtype([(n, order + t) for n, t in props])
        arr = np.frombuffer(body, dtype=dtype, count=count)
        col = {n: arr[n].astype(float) for n in names}
    points = np.column_stack((col["x"], col["y"], col["z"]))
    colours = None
    if all(k in col for k in ("red", "green", "blue")):
        rgb = np.column_stack((col["red"], col["green"], col["blue"]))
        colours = rgb / (255.0 if rgb.max() > 1.0 else 1.0)
    return PointCloud(points, colours)


def read_las(data):
    """A LAS's points (scaled and offset as it says) and their colours (formats with RGB)."""
    if data[:4] != b"LASF":
        raise ValueError("not a LAS")
    major, minor = data[24], data[25]
    offset = struct.unpack_from("<I", data, 96)[0]
    point_format = data[104] & 0x3F                         # (the top bits: compression flags)
    record = struct.unpack_from("<H", data, 105)[0]
    count = struct.unpack_from("<I", data, 107)[0]
    if (major, minor) >= (1, 4) and count == 0:
        count = struct.unpack_from("<Q", data, 247)[0]
    scale = struct.unpack_from("<3d", data, 131)
    shift = struct.unpack_from("<3d", data, 155)
    count = min(count, (len(data) - offset) // record)
    raw = np.frombuffer(data, dtype=np.uint8, count=count * record, offset=offset).reshape(count, record)
    xyz = raw[:, :12].copy().view("<i4").reshape(count, 3).astype(float)
    points = xyz * np.array(scale) + np.array(shift)
    colours = None
    at = LAS_RGB.get(point_format)
    if at is not None and record >= at + 6:
        rgb = raw[:, at:at + 6].copy().view("<u2").reshape(count, 3).astype(np.float32)
        top = float(rgb.max()) if len(rgb) else 0.0
        colours = rgb / (65535.0 if top > 255 else 255.0) if top > 0 else None
    return PointCloud(points, colours)


def read_las_file(path, most=None):
    """A LAS file's points without reading it all into memory (mapped): every k-th record when it has more than
    `most`."""
    data = np.memmap(path, dtype=np.uint8, mode="r")
    head = bytes(data[:375])
    if head[:4] != b"LASF":
        raise ValueError("not a LAS")
    offset = struct.unpack_from("<I", head, 96)[0]
    record = struct.unpack_from("<H", head, 105)[0]
    count = struct.unpack_from("<I", head, 107)[0]
    if (head[24], head[25]) >= (1, 4) and count == 0:
        count = struct.unpack_from("<Q", head, 247)[0]
    count = min(count, (len(data) - offset) // record)
    step = max(1, int(np.ceil(count / most))) if most else 1
    rows = data[offset:offset + count * record].reshape(count, record)[::step]
    fake = bytearray(bytes(data[:offset]))                  # (its header and records, with the count it now has)
    struct.pack_into("<I", fake, 107, len(rows))
    if (head[24], head[25]) >= (1, 4):
        struct.pack_into("<Q", fake, 247, len(rows))
    return read_las(bytes(fake) + np.ascontiguousarray(rows).tobytes())


def read_laz_file(path, most=None):
    """(0.284) A LAZ's (or LAS's) points, decompressed by laspy (lazrs), scaled and offset as it says, with its
    colours — every k-th when it has more than `most`, read a chunk at a time (not all of it in memory)."""
    try:
        import laspy
    except ImportError:
        raise ValueError("laz") from None
    with laspy.open(path) as reader:
        count = int(reader.header.point_count)
        step = max(1, int(np.ceil(count / most))) if most else 1
        points, colours = [], []
        for chunk in reader.chunk_iterator(1_000_000):
            pts = np.column_stack((np.asarray(chunk.x), np.asarray(chunk.y), np.asarray(chunk.z)))[::step]
            points.append(pts)
            names = set(chunk.point_format.dimension_names)
            if {"red", "green", "blue"} <= names:
                colours.append(np.column_stack((np.asarray(chunk.red), np.asarray(chunk.green),
                                                np.asarray(chunk.blue))).astype(np.float32)[::step])
    pts = np.concatenate(points) if points else np.zeros((0, 3))
    rgb = np.concatenate(colours) if colours and len(colours) == len(points) else None
    if rgb is not None:
        top = float(rgb.max()) if len(rgb) else 0.0
        rgb = rgb / (65535.0 if top > 255 else 255.0) if top > 0 else None
    return PointCloud(pts, rgb)


def read_e57_file(path, most=None):
    """(0.284) An E57's points — every scan in it, each placed by its pose (pye57: scans in the file's frame) — and
    their colours when it has them; at most `most`, thinned evenly."""
    try:
        import pye57
    except ImportError:
        raise ValueError("e57") from None
    e57 = pye57.E57(path)
    points, colours = [], []
    for k in range(e57.scan_count):
        header = e57.get_header(k)
        fields = set(header.point_fields)
        rgb = {"colorRed", "colorGreen", "colorBlue"} <= fields
        data = e57.read_scan(k, ignore_missing_fields=True, colors=rgb, transform=True)
        pts = np.column_stack((data["cartesianX"], data["cartesianY"], data["cartesianZ"]))
        points.append(pts)
        if rgb:
            colours.append(np.column_stack((data["colorRed"], data["colorGreen"],
                                            data["colorBlue"])).astype(np.float32) / 255.0)
    pts = np.concatenate(points) if points else np.zeros((0, 3))
    rgb = np.concatenate(colours) if colours and len(colours) == len(points) else None
    cloud = PointCloud(pts, rgb)
    return cloud.thinned(most) if most else cloud


def read_file(path, most=None):
    """The point cloud of a file, by its extension (at most `most` points: thinned evenly)."""
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "las":
        return read_las_file(path, most)
    if ext == "laz":
        return read_laz_file(path, most)
    if ext == "e57":
        return read_e57_file(path, most)
    with open(path, "rb") as f:
        data = f.read()
    if ext == "ply":
        cloud = read_ply(data)
    else:
        cloud = read_text(data.decode("utf-8", errors="replace"))
    return cloud.thinned(most) if most else cloud
