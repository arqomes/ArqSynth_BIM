"""(0.472) The company's title block kept in the ArqSynth suite's folder (arqsynth_templates.paths.suite_dir()), so that
every new project — and the suite's other programs — can use the office's own: carimbo.json (sheets.clean_company's
data) and its logo copied beside it (carimbo_logotipo.<ext>), so the logo is not lost when the original file moves."""

import json
import os
import shutil

FILE = "carimbo.json"
LOGO = "carimbo_logotipo"


def _folder():
    from arqsynth_templates.paths import suite_dir
    return suite_dir()


def path():
    return os.path.join(_folder(), FILE)


def load():
    """The company's title block saved (sheets.clean_company), or None."""
    from . import sheets
    try:
        with open(path(), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    company = sheets.clean_company(data)
    if company is not None and company["logo"] and not os.path.isabs(company["logo"]):
        company["logo"] = os.path.join(_folder(), company["logo"])
    return company


def save(company):
    """The company's title block saved for every project (its logo copied beside it). Returns the file's path."""
    from . import sheets
    company = sheets.clean_company(company)
    if company is None:
        raise ValueError("company_title_block")
    folder = _folder()
    os.makedirs(folder, exist_ok=True)
    data = dict(company)
    logo = company["logo"]
    if logo and os.path.exists(logo):
        ext = os.path.splitext(logo)[1].lower() or ".png"
        target = os.path.join(folder, LOGO + ext)
        if os.path.abspath(logo) != os.path.abspath(target):
            shutil.copy2(logo, target)
        data["logo"] = LOGO + ext                 # (beside the file: the folder may be shared)
    with open(path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return path()
