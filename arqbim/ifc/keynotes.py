"""Keynotes (0.194), mixed into IfcModel: an IfcClassificationReference of the classification "Notas-chave" (its
Identification the code, its Name the text), on the element's type — so every element of that type has it — or on
the element when it has no type. Read through the type (an element's own one first).

(0.248) The project's own table: references of that classification that belong to no element, marked as its entries
(Description TABLE_MARK) — a code and its text, offered beside the program's table; a code's text changed there is
the text of the elements that have it."""

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.api.classification
import ifcopenshell.util.classification
import ifcopenshell.util.element

from ..model.keynotes import CLASSIFICATION

api = ifcopenshell.api
TABLE_MARK = "ArqSynth: tabela de notas-chave do projeto"


class KeynoteMixin:
    def _table_refs(self):
        c = self._keynote_classification()
        if c is None:
            return {}
        return {r.Identification: r for r in self.file.by_type("IfcClassificationReference")
                if r.ReferencedSource == c and r.Description == TABLE_MARK and r.Identification}

    def keynote_table(self):
        """(0.248) {code: text} of the project's own keynote table."""
        return {code: r.Name or "" for code, r in self._table_refs().items()}

    def set_keynote_table(self, entries):
        """(0.248) The project's own keynote table made `entries` {code: text}: entries added, their text changed —
        the elements with that code take it too —, or taken away (the elements keep theirs)."""
        entries = {str(k).strip(): str(v).strip() for k, v in entries.items() if str(k).strip()}
        current = self._table_refs()
        for code, r in current.items():
            if code not in entries:                       # (one the elements share — IfcOpenShell keeps one per
                if r.ClassificationRefForObjects:         # code —: it stays theirs, out of the table)
                    r.Description = None
                else:
                    self.file.remove(r)
        if not entries:
            return
        c = self._keynote_classification(True)
        for code, text in entries.items():
            r = current.get(code)
            if r is None:
                self.file.createIfcClassificationReference(None, code, text, c, TABLE_MARK, None)
            elif r.Name != text:
                r.Name = text
        for r in self.file.by_type("IfcClassificationReference"):          # (the elements' with those codes)
            if r.ReferencedSource == c and r.Description != TABLE_MARK and r.Identification in entries:
                if r.Name != entries[r.Identification]:
                    r.Name = entries[r.Identification]

    def _keynote_classification(self, make=False):
        for c in self.file.by_type("IfcClassification"):
            if c.Name == CLASSIFICATION:
                return c
        return api.classification.add_classification(self.file, classification=CLASSIFICATION) if make else None

    def _keynote_refs(self, product, inherit):
        refs = ifcopenshell.util.classification.get_references(product, should_inherit=inherit)
        return [r for r in refs if getattr(r, "ReferencedSource", None) is not None
                and getattr(r.ReferencedSource, "Name", None) == CLASSIFICATION]

    def keynote_of(self, guid):
        """(code, text) of an element's keynote — its own, else its type's — or None."""
        e = self.by_guid(guid)
        if e is None:
            return None
        refs = self._keynote_refs(e, inherit=False) or self._keynote_refs(e, inherit=True)
        if not refs:
            return None
        r = sorted(refs, key=lambda r: r.id())[0]
        return (r.Identification or "", r.Name or "")

    def keynote_holder(self, guid):
        """What carries an element's keynote: its type, or the element when it has none."""
        e = self.by_guid(guid)
        return ifcopenshell.util.element.get_type(e) or e

    def set_keynote(self, guid, code, text=""):
        """An element's keynote (on its type, else on it): `code` with its text; None or "" takes it away."""
        holder = self.keynote_holder(guid)
        for r in self._keynote_refs(holder, inherit=False):
            self._unlink_keynote(r, holder)
        e = self.by_guid(guid)
        if holder is not e:                          # (one the element had of its own goes too: the type's rules)
            for r in self._keynote_refs(e, inherit=False):
                self._unlink_keynote(r, e)
        if code:
            api.classification.add_reference(self.file, products=[holder], identification=str(code),
                                             name=str(text or ""), classification=self._keynote_classification(True))

    def _unlink_keynote(self, r, product):
        """A keynote's reference taken off `product` — (0.248) one of the project's table stays there, unused
        (IfcOpenShell's remove_reference deletes a reference nothing uses)."""
        if r.Description != TABLE_MARK:
            api.classification.remove_reference(self.file, reference=r, products=[product])
            return
        for rel in list(r.ClassificationRefForObjects or ()):
            rest = [o for o in rel.RelatedObjects if o != product]
            if rest:
                rel.RelatedObjects = rest
            else:
                self.file.remove(rel)

    def keynote_sharers(self, guid):
        """The elements whose keynote changes with this one's: those of its type (itself if it has none)."""
        holder = self.keynote_holder(guid)
        if holder.is_a("IfcTypeObject"):
            return [o.GlobalId for o in ifcopenshell.util.element.get_types(holder)]
        return [guid]
