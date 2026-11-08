"""(0.472) The company's title block kept in the ArqSynth suite's folder (arqsynth_templates.paths.suite_dir()), so that
every new project — and the suite's other programs — can use the office's own: carimbo.json (sheets.clean_company's
data). (0.473) Its pictures (the logo…) are copied beside it, named by what they hold (carimbo_<…>.<ext>), so they are
not lost when the original files move, nor taken for one another."""

import copy
import hashlib
import json
import os
import shutil

FILE = "carimbo.json"
PICTURE = "carimbo_"


def _folder():
    from arqsynth_templates.paths import suite_dir
    return suite_dir()


def path():
    return os.path.join(_folder(), FILE)


def load():
    """The company's title block saved (sheets.clean_company), its pictures found beside it; None if there is none."""
    from . import sheets
    try:
        with open(path(), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if isinstance(data, dict) and data.get("logo") and not os.path.isabs(str(data["logo"])):
        data["logo"] = os.path.join(_folder(), str(data["logo"]))           # (0.472's file: its logo beside it)
    company = sheets.clean_company(data)
    for item in company["items"] if company is not None else ():
        if item["kind"] == "image" and item["path"] and not os.path.isabs(item["path"]):
            item["path"] = os.path.join(_folder(), item["path"])
    return company


def _stored(source, folder):
    """A picture copied into the folder under a name made of what it holds; its name there."""
    with open(source, "rb") as f:
        digest = hashlib.sha1(f.read()).hexdigest()[:12]
    name = PICTURE + digest + (os.path.splitext(source)[1].lower() or ".png")
    target = os.path.join(folder, name)
    if os.path.abspath(source) != os.path.abspath(target) and not os.path.exists(target):
        shutil.copy2(source, target)
    return name


def save(company):
    """The company's title block saved for every project (its pictures copied beside it). Returns the file's path."""
    from . import sheets
    company = sheets.clean_company(company)
    if company is None:
        raise ValueError("company_title_block")
    folder = _folder()
    os.makedirs(folder, exist_ok=True)
    data = copy.deepcopy(company)
    for item in data["items"]:
        if item["kind"] == "image" and item["path"] and os.path.isfile(item["path"]):
            item["path"] = _stored(item["path"], folder)         # (beside the file: the folder may be shared)
    with open(path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return path()
