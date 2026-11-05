"""(0.393) The ArqSynth templates («Arquivo Modelo», arqsynth_templates) — Phase 1: the TemplateManager and the factory
template. Each test in a folder of its own (never the user's): the first start with no folder, saving and reading,
updating (another program's data kept), each program's default, a broken file, the default deleted by hand, missing
and wrong fields, an older and a newer format, the factory protected, safe writing, a ZIP with textures, copies and
renames, two programs at once."""

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from arqsynth_templates import (FACTORY_ID, FACTORY_NAME, DefaultLost, Filled, Notice, TemplateError,  # noqa: E402
                                TemplateManager, manager as manager_module, paths, problems)

FACTORY = {"name": FACTORY_NAME, "id": FACTORY_ID, "version": 1, "programs": ["arqsynth-bim"],
           "units": {"system": "metric", "length": "m", "decimals": 2, "decimal_separator": ","},
           "project": {"name": "Projeto", "site": "Terreno", "building": "Edifício", "ifc_schema": "IFC4"},
           "storeys": [{"name": "Térreo", "elevation": 0.0, "height": 3.0}],
           "materials": [{"key": "reboco", "name": "Reboco", "color": "#eee8db", "category": "plaster"}],
           "types": {"wall": [{"key": "parede_20", "name": "Parede 20", "layers": [
               {"material": "reboco", "thickness": 0.02, "function": "finish1"},
               {"material": "bloco", "thickness": 0.16, "function": "structure"}]}]},
           "ifc_classes": {"wall": "IfcWall"},
           "dimensions": {"text": 2.2, "mark": "tick", "unit": "m", "decimals": 2},
           "interface": {"theme": "light", "start_page": True}}


class Templates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "ArqSynth")          # (not there yet: the first start)
        self.bim = TemplateManager("arqsynth-bim", FACTORY, root=self.root, program_version="0.393.0")

    def tearDown(self):
        self.tmp.cleanup()

    def data(self, **changes):
        made = self.bim.factory().data
        made.pop("id")
        made.update(changes)
        return made

    def test_first_start_without_folder(self):
        self.assertFalse(os.path.exists(self.root))
        listed = self.bim.list()
        self.assertEqual([(e.name, e.is_factory, e.is_default) for e in listed], [(FACTORY_NAME, True, True)])
        made = self.bim.get_default()
        self.assertTrue(made.is_factory and not made.notices)
        self.assertEqual(made.data["units"]["decimals"], 2)
        self.bim.ensure()
        self.assertTrue(os.path.isdir(os.path.join(self.root, "templates")))

    def test_save_load_update(self):
        units = dict(FACTORY["units"], length="cm", decimals=1)
        saved = self.bim.save(self.data(units=units), "Escritório")
        self.assertEqual(os.path.basename(saved.path), "Escritório.astpl")
        with open(saved.path, encoding="utf-8") as f:
            raw = json.load(f)                                     # (plain JSON: any program reads it)
        self.assertEqual((raw["format"], raw["schema_version"], raw["version"]), ("arqsynth-template", 1, 1))
        self.assertNotEqual(raw["id"], FACTORY_ID)
        self.assertIn("arqsynth-bim", raw["programs"])
        again = self.bim.load("escritório")                        # (the name, capitals aside)
        self.assertEqual((again.data["units"]["length"], again.data["units"]["decimals"], again.notices), ("cm", 1, []))
        with self.assertRaises(TemplateError) as made:
            self.bim.save(self.data(), "Escritório")
        self.assertEqual(made.exception.code, "exists")
        cad = TemplateManager("arqsynth-cad", FACTORY, root=self.root)    # (another program of the suite…)
        data = cad.load("Escritório").data
        data["extensions"] = {"arqsynth-cad": {"layers": ["A-WALL"]}}
        cad.update("Escritório", data)
        mine = self.bim.load("Escritório").data
        mine["units"]["decimals"] = 2
        mine["extensions"] = {}
        updated = self.bim.update("Escritório", mine)              # (…its data kept when this one saves it)
        self.assertEqual((updated.version, updated.id), (3, raw["id"]))
        self.assertEqual(self.bim.load("Escritório").data["extensions"]["arqsynth-cad"], {"layers": ["A-WALL"]})
        self.assertEqual(sorted(self.bim.load("Escritório").data["programs"]), ["arqsynth-bim", "arqsynth-cad"])

    def test_defaults_of_two_programs(self):
        self.bim.save(self.data(), "Moradias")
        self.bim.save(self.data(), "Escolas")
        cad = TemplateManager("arqsynth-cad", FACTORY, root=self.root)
        self.bim.set_default("Moradias")
        cad.set_default("Escolas")
        self.assertEqual((self.bim.get_default().name, cad.get_default().name), ("Moradias", "Escolas"))
        with open(os.path.join(self.root, "settings.json"), encoding="utf-8") as f:
            settings = json.load(f)
        self.assertEqual(sorted(settings["defaults"]), ["arqsynth-bim", "arqsynth-cad"])
        self.assertEqual([e.name for e in self.bim.list() if e.is_default], ["Moradias"])
        self.bim.reset_factory()
        self.assertTrue(self.bim.get_default().is_factory)
        self.assertEqual(cad.get_default().name, "Escolas")

    def test_broken_file(self):
        self.bim.ensure()
        path = os.path.join(self.root, "templates", "Estragado.astpl")
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"format": "arqsynth-template", "name": "Estragado", "units": {')
        broken = [e for e in self.bim.list() if not e.ok]
        self.assertEqual([e.name for e in broken], ["Estragado"])
        self.assertIn("estragado", broken[0].problem)
        with self.assertRaises(TemplateError) as made:
            self.bim.load("Estragado")
        self.assertEqual(made.exception.code, "corrupted")
        with open(os.path.join(self.root, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"defaults": {"arqsynth-bim": {"name": "Estragado"}}}, f)
        made = self.bim.get_default()
        self.assertTrue(made.is_factory)
        self.assertEqual(made.notices, [DefaultLost("Estragado", "corrupted")])
        self.assertIn("estragado", made.messages()[0])
        with open(os.path.join(self.root, "settings.json"), "w", encoding="utf-8") as f:
            f.write("nada")                                         # (settings.json broken: the factory's)
        self.assertTrue(self.bim.get_default().is_factory)

    def test_default_deleted_by_hand(self):
        saved = self.bim.save(self.data(), "Escritório")
        self.bim.set_default("Escritório")
        os.remove(saved.path)
        made = self.bim.get_default()
        self.assertTrue(made.is_factory)
        self.assertEqual(made.notices, [DefaultLost("Escritório", "not_found")])
        self.assertTrue(self.bim.list()[0].is_default)

    def test_missing_and_wrong_fields(self):
        self.bim.ensure()
        layers = [{"material": "reboco", "thickness": -1}]
        little = {"format": "arqsynth-template", "schema_version": 1, "name": "Pouco", "version": 1,
                  "units": {"length": "cm", "decimals": "dois"},
                  "types": {"wall": [{"key": "boa", "name": "Boa", "layers": [{"material": "bloco", "thickness": 0.2}]},
                                     {"key": "má", "name": "Má", "layers": layers}]}}
        with open(os.path.join(self.root, "templates", "Pouco.astpl"), "w", encoding="utf-8") as f:
            json.dump(little, f)
        made = self.bim.load("Pouco")
        self.assertEqual(made.data["units"]["length"], "cm")                       # (its own kept)
        self.assertEqual(made.data["units"]["decimals"], 2)                        # (wrong: the factory's)
        self.assertEqual([t["key"] for t in made.data["types"]["wall"]], ["boa"])  # (a wrong type left out)
        self.assertEqual(made.data["storeys"], FACTORY["storeys"])                 # (missing: the factory's)
        self.assertIn(Filled("units.decimals"), made.notices)
        self.assertIn(Filled("types.wall[1]", removed=True), made.notices)
        self.assertIn(Filled("storeys"), made.notices)
        self.assertEqual(problems(made.data), [])
        self.assertTrue(all(m for m in made.messages()))

    def test_older_and_newer_format(self):
        self.bim.ensure()
        old = {"name": "Antigo", "units": "mm", "storeys": [{"name": "Cave", "level": -3.0}],
               "materials": [{"key": "cal", "name": "Cal", "color": [1.0, 1.0, 1.0]}]}
        with open(os.path.join(self.root, "templates", "Antigo.astpl"), "w", encoding="utf-8") as f:
            json.dump(old, f)
        made = self.bim.load("Antigo")
        self.assertEqual(made.notices[0], Notice("migrated", "0"))
        self.assertEqual((made.data["schema_version"], made.data["units"]["length"]), (1, "mm"))
        self.assertEqual(made.data["storeys"], [{"name": "Cave", "elevation": -3.0}])
        self.assertEqual(made.data["materials"][0]["color"], "#ffffff")
        new = dict(self.data(), name="Futuro", schema_version=7, version=1, futuro={"x": 1})
        with open(os.path.join(self.root, "templates", "Futuro.astpl"), "w", encoding="utf-8") as f:
            json.dump(new, f)
        made = self.bim.load("Futuro")
        self.assertEqual(made.notices[0], Notice("newer", "7"))
        self.assertEqual(made.data["futuro"], {"x": 1})                             # (what it does not know: kept)
        with self.assertRaises(TemplateError) as refused:
            self.bim.update("Futuro", made.data)
        self.assertEqual(refused.exception.code, "newer")
        self.assertEqual(self.bim.save(made.data, "Futuro (cópia)").data["futuro"], {"x": 1})

    def test_factory_protected(self):
        for call in (lambda: self.bim.delete(FACTORY_NAME), lambda: self.bim.rename(FACTORY_NAME, "Outro"),
                     lambda: self.bim.update(FACTORY_NAME, self.data()), lambda: self.bim.save(self.data(), FACTORY_NAME),
                     lambda: self.bim.save(self.data(), "arqsynth padrão")):
            with self.assertRaises(TemplateError) as made:
                call()
            self.assertEqual(made.exception.code, "factory")
        copy = self.bim.duplicate(FACTORY_NAME, "Cópia")
        self.assertNotEqual(copy.id, FACTORY_ID)
        self.assertEqual(copy.version, 1)

    def test_safe_writing(self):
        saved = self.bim.save(self.data(), "Escritório")
        with open(saved.path, "rb") as f:
            before = f.read()
        with mock.patch.object(manager_module.os, "replace", side_effect=OSError("o programa fechou a meio")):
            with self.assertRaises(OSError):
                data = self.bim.load("Escritório").data
                data["units"]["decimals"] = 4
                self.bim.update("Escritório", data)
        with open(saved.path, "rb") as f:
            self.assertEqual(f.read(), before)                      # (the old one whole)
        self.assertEqual([n for n in os.listdir(os.path.dirname(saved.path)) if not n.startswith(".")],
                         ["Escritório.astpl"])                      # (no half-written file left)
        self.assertEqual([e.name for e in self.bim.list()], [FACTORY_NAME, "Escritório"])

    def test_zip_with_textures(self):
        data = self.data()
        data["materials"][0]["texture"] = "reboco.png"
        saved = self.bim.save(data, "Com textura", assets={"reboco.png": b"\x89PNG..."})
        with open(saved.path, "rb") as f:
            self.assertEqual(f.read(2), b"PK")
        made = self.bim.load("Com textura")
        self.assertEqual(made.assets, {"reboco.png": b"\x89PNG..."})
        self.assertEqual(made.data["materials"][0]["texture"], "reboco.png")

    def test_copy_rename_delete(self):
        self.bim.save(self.data(), "Moradias")
        self.bim.set_default("Moradias")
        renamed = self.bim.rename("Moradias", "Moradias T3")
        self.assertEqual(os.path.basename(renamed.path), "Moradias T3.astpl")
        self.assertEqual(self.bim.get_default().name, "Moradias T3")      # (the default follows)
        self.assertEqual([e.name for e in self.bim.list()], [FACTORY_NAME, "Moradias T3"])
        copy = self.bim.duplicate("Moradias T3", "Moradias T4")
        self.assertNotEqual(copy.id, renamed.id)
        self.bim.delete("Moradias T3")
        self.assertTrue(self.bim.get_default().is_factory and not self.bim.get_default().notices)
        with self.assertRaises(TemplateError) as made:
            self.bim.rename("Moradias T4", "a\x01b")
        self.assertEqual(made.exception.code, "name")

    def test_two_programs_at_once(self):
        self.bim.save(self.data(), "Comum")
        cad = TemplateManager("arqsynth-cad", FACTORY, root=self.root)
        errors = []

        def work(manager, k):
            try:
                for n in range(5):
                    manager.save(self.data(), "{} {} {}".format(manager.program, k, n))
                    manager.set_default("Comum")
                    self.assertEqual(manager.load("Comum").name, "Comum")
            except Exception as exc:                                # pragma: no cover (said below)
                errors.append(exc)
        threads = [threading.Thread(target=work, args=(m, k)) for k, m in enumerate((self.bim, cad, self.bim, cad))]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(self.bim.list()), 1 + 1 + 20)
        with open(os.path.join(self.root, "settings.json"), encoding="utf-8") as f:
            self.assertEqual(sorted(json.load(f)["defaults"]), ["arqsynth-bim", "arqsynth-cad"])
        lock = os.path.join(self.root, "settings.json.lock")       # (a lock left by a program that stopped)
        with open(lock, "w") as f:
            f.write("1")
        old = time.time() - 60
        os.utime(lock, (old, old))
        self.bim.set_default("Comum")
        self.assertFalse(os.path.exists(lock))

    def test_suite_folder(self):
        with mock.patch.dict(os.environ, {"ARQSYNTH_HOME": self.root}):
            self.assertEqual(paths.suite_dir(), os.path.abspath(self.root))
            self.assertEqual(paths.templates_dir(), os.path.join(os.path.abspath(self.root), "templates"))

    def test_documented_example(self):
        """The example beside the format's description (exemplo.astpl) is a right template, read without a notice
        by a program whose factory has the same sections."""
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "arqsynth_templates")
        with open(os.path.join(here, "exemplo.astpl"), encoding="utf-8") as f:
            example = json.load(f)
        self.assertEqual(problems(example), [])
        made = self.bim.prepare(example)
        self.assertEqual([n for n in made.notices if not isinstance(n, Filled)], [])
        self.assertEqual(made.data["extensions"]["arqsynth-cad"], {"layers": ["A-WALL", "A-DOOR"]})

    def test_bim_factory(self):
        from arqbim.model import project_templates
        made = project_templates.factory()
        self.assertEqual(problems(made), [])
        self.assertEqual((made["name"], made["id"]), (FACTORY_NAME, FACTORY_ID))
        self.assertTrue({"wall", "slab", "roof", "door", "window"} <= set(made["types"]))
        door = made["types"]["door"][0]
        self.assertTrue(door["design"]["rows"] and door["width"] > 0)
        self.assertTrue(any(m["key"] == "tinta_branca" for m in made["materials"]))
        bim = project_templates.manager(root=self.root)
        self.assertEqual(bim.get_default().data, made | {"format": "arqsynth-template"})


if __name__ == "__main__":
    unittest.main()
