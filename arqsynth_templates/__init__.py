"""ArqSynth templates («Arquivo Modelo»): the settings a new project starts with, kept in the suite's shared folder
as .astpl files (JSON, or a ZIP with the JSON and its textures) that any program of the suite — or another — can
read; schema.json documents the format. Plain Python (3.8+), nothing to install: copy this folder into another
program to use it.

    from arqsynth_templates import TemplateManager
    manager = TemplateManager("arqsynth-cad", factory=MY_FACTORY)
    template = manager.get_default()          # the default (or the factory's, said in template.notices)
    manager.save(data, "Escritório")          # a new template; update(), delete(), set_default()…
"""

from .manager import (EXTENSION, FACTORY_ID, FACTORY_NAME, FORMAT, DefaultLost, Entry, Filled, Template,
                      TemplateError, TemplateManager, file_name, read_file, write_atomic)
from .migrate import SCHEMA_VERSION, Notice
from .paths import settings_file, suite_dir, templates_dir
from .validate import Problem, problems, schema

__all__ = ["EXTENSION", "FACTORY_ID", "FACTORY_NAME", "FORMAT", "SCHEMA_VERSION", "DefaultLost", "Entry", "Filled",
           "Notice", "Problem", "Template", "TemplateError", "TemplateManager", "file_name", "problems", "read_file",
           "schema", "settings_file", "suite_dir", "templates_dir", "write_atomic"]
