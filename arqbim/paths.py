"""Where the program keeps its own files (0.77): the log, the geometry cache, the local copies of shared
projects — in a folder named after the brand, "ArqSynth BIM". Until 0.76 it was "ArqBIM": that folder is
renamed once, the first time (everything in it kept); if it cannot be (in use), it goes on being used."""

import os

FOLDER = "ArqSynth BIM"
LEGACY_FOLDER = "ArqBIM"


def user_dir(base, *parts):
    """`base`/ArqSynth BIM/parts…, made from `base`/ArqBIM when only that one is there."""
    new, old = os.path.join(base, FOLDER), os.path.join(base, LEGACY_FOLDER)
    if not os.path.exists(new) and os.path.isdir(old):
        try:
            os.rename(old, new)
        except OSError:                       # (open in another window of the program: keep using it)
            return os.path.join(old, *parts)
    return os.path.join(new, *parts)


def local_base():
    """The user's application data folder (Windows' LOCALAPPDATA; the home folder elsewhere)."""
    return os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
