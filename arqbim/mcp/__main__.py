"""python -m arqbim.mcp [--file model.ifc | --live]: the program's MCP server on stdin / stdout (0.268).

(0.269) With the program open and «Ligação à IA» on, the tools work on the model in its window (seen as they work,
undone there too); --file: on that IFC file, with no window; neither: the window if it answers, else a new model."""

import argparse
import sys

from .. import __version__
from . import link
from .protocol import Server
from .tools import INSTRUCTIONS, Session, linked_tools, tools


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m arqbim.mcp", description="ArqSynth BIM's MCP server (stdio).")
    parser.add_argument("--file", help="the IFC model to open, with no window")
    parser.add_argument("--live", action="store_true", help="the model open in the program's window")
    args = parser.parse_args(argv)
    found = None if args.file else link.read()
    if args.live or (found is not None and link.alive(found)):
        offered = linked_tools()
    else:
        offered = tools(Session(args.file))
    Server("arqsynth-bim", __version__, offered, INSTRUCTIONS).serve()
    return 0


if __name__ == "__main__":
    sys.exit(main())
