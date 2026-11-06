"""ArqSynth BIM (until 0.76: ArqBIM): native-IFC BIM modeller (standalone desktop app).

    core/    pure logic: units, polygon meshes, sketch geometry, inferences (no UI, no GPU)
    model/   the open document and its undo/redo commands
    ifc/     the IFC model (the only package that imports IfcOpenShell)
    render/  GPU viewport (wgpu via pygfx), kept behind one class so it can be replaced
    tools/   interactive tools (Select, Line, Rectangle, Push/Pull, Move, Rotate, Tape, Wall, Slab, Door, Window)
    ui/      Qt main window, toolbar, status bar, properties panel
"""

__version__ = "0.423.0"
