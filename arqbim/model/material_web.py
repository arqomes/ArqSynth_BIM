"""(0.471) Materials from the web (the owner: «Sim, liga» — Poly Haven's free textures in the Materials panel, as its
models in the Library since 0.467): the list of Poly Haven's textures (CC0: free for any use, the public domain), the
pictures of one — its colour, its relief (normal map, OpenGL's), its roughness, its ambient occlusion, and a metal's
metallic (the blue of its «arm» picture) — and the project's material made of them: named as Poly Haven names it, of the
category its own say, its shading colour the colour picture's average, its pictures as big in the model as the real
thing they were taken of (Poly Haven gives it, in millimetres). Pure data, no Qt (the panel fetches)."""

import json

from ..core import pbr
from . import component_library as lib

RESOLUTION = "1k"                 # (light: a material of a model, not a render's close-up)
# Poly Haven's maps -> the look's slots (its «arm»: occlusion, roughness, metallic in red, green, blue)
MAPS = {"Diffuse": "base", "nor_gl": "normal", "Rough": "roughness", "AO": "ao"}
# Poly Haven's categories -> the material's category (what it is cut with, its family), the first found
CATEGORIES = (("brick", "brick"), ("concrete", "concrete"), ("plaster-concrete", "concrete"), ("plaster", "plaster"),
              ("wood", "wood"), ("raw wood", "wood"), ("bark", "wood"), ("tiles", "ceramic"), ("roofing", "ceramic"),
              ("metal", "steel"), ("rock", "stone"), ("sandstone", "stone"), ("cobblestone", "stone"),
              ("fabric", "fabric"), ("cotton", "fabric"), ("denim", "fabric"), ("leather", "fabric"),
              ("sand", "earth"), ("gravel", "earth"), ("terrain", "earth"), ("asphalt", "concrete"),
              ("road", "concrete"))
SKIPPED = ("collection:",)        # (Poly Haven's collections are not kinds of material)
FILTERS = ("brick", "wood", "concrete", "plaster", "tiles", "rock", "metal", "fabric", "floor", "wall", "roofing",
           "terrain", "asphalt", "cobblestone", "sand", "gravel", "leather")


def rows(text):
    """Poly Haven's textures (its /assets?type=textures, JSON): [{id, name, authors, categories, dims (w, h m),
    thumbnail, page}] by name."""
    data = json.loads(text)
    out = []
    for key, asset in (data.items() if isinstance(data, dict) else ()):
        if not isinstance(asset, dict):
            continue
        thumb = str(asset.get("thumbnail_url") or "")
        thumb = thumb.replace("format=webp", "format=png") if thumb else \
            "https://cdn.polyhaven.com/asset_img/thumbs/{}.png?width=256&height=256".format(key)
        dims = asset.get("dimensions") or (1000, 1000)
        try:
            w, h = (max(float(dims[0]) / 1000.0, 0.01), max(float(dims[1]) / 1000.0, 0.01))
        except (TypeError, ValueError, IndexError):
            w = h = 1.0
        categories = [str(c) for c in asset.get("categories") or () if not str(c).startswith(SKIPPED)]
        authors = asset.get("authors") or {}
        out.append({"id": key, "name": str(asset.get("name") or key), "categories": categories, "dims": (w, h),
                    "authors": ", ".join(authors) if isinstance(authors, (dict, list)) else str(authors),
                    "thumbnail": thumb, "page": "{}/a/{}".format(lib.POLYHAVEN_SITE, key)})
    return sorted(out, key=lambda r: r["name"].lower())


def files(text, resolution=RESOLUTION):
    """A texture's pictures to fetch (its /files/{id}, JSON): {slot or «arm»: address} — JPEG, at `resolution` (else
    the lightest it has)."""
    data = json.loads(text)
    out = {}
    for name, slot in tuple(MAPS.items()) + (("arm", "arm"),):
        entry = data.get(name) if isinstance(data, dict) else None
        if not isinstance(entry, dict):
            continue
        for res in (resolution,) + tuple(k for k in lib.RESOLUTIONS if k != resolution):
            url = ((entry.get(res) or {}).get("jpg") or {}).get("url")
            if url:
                out[slot] = str(url)
                break
    return out


def category_of(row):
    """The material's category of a texture (its first Poly Haven category that says one), or ""."""
    names = set(row.get("categories") or ())
    return next((ours for theirs, ours in CATEGORIES if theirs in names), "")


def is_metal(row):
    return "metal" in (row.get("categories") or ())


def look_of(row, paths):
    """The realistic look of a texture fetched — paths: {slot: its file} (base, normal, roughness, ao, metallic) — as
    big in the model as the real thing, a metal metallic, a cloth a cloth; the roughness and metallic values 50 %: the
    pictures as they are."""
    preset = "metal" if is_metal(row) else "cloth" if category_of(row) == "fabric" else "matte"
    look = pbr.preset(preset)
    for slot in pbr.SLOTS:
        if paths.get(slot):
            look = look.with_map(slot, paths[slot])
    w, h = row.get("dims") or (1.0, 1.0)
    from dataclasses import replace
    return replace(look, width=float(w), height_m=float(h),
                   roughness=pbr.AS_PICTURE if paths.get("roughness") else look.roughness,
                   metallic=pbr.AS_PICTURE if paths.get("metallic") else look.metallic)


def material(row, paths, colour, name):
    """The project's material of a texture fetched (its key "m:new": the window names it), named `name`, its shading
    colour `colour` (sRGB 0–1: the colour picture's average)."""
    from ..ifc import catalog
    look = look_of(row, paths)
    return catalog.MaterialSpec("m:new", name, name, category_of(row), tuple(float(c) for c in colour),
                                finish=pbr.finish_of(look), look=look)
