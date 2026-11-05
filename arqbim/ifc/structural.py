"""The analytical model in the IFC (0.163, Phase 9, step 1): an IfcStructuralAnalysisModel (LOADING_3D) of the
building — its nodes IfcStructuralPointConnection (a vertex), the supports their IfcBoundaryNodeCondition (fixed:
the six stiffnesses true; pinned: the three translations), its columns and beams IfcStructuralCurveMember
(RIGID_JOINED_MEMBER, an edge between two of those vertices) each joined to its nodes (IfcRelConnectsStructuralMember)
and to the physical element it stands for (IfcRelAssignsToProduct), its slabs IfcStructuralSurfaceMember
(BENDING_ELEMENT, a face at their level, their thickness). Topology in the "Reference" representation of a
GRAPH_VIEW context, as analysis programs read it. Made again whole each time (the old one, made by this program,
taken away first)."""

import numpy as np

import ifcopenshell.api as api
import ifcopenshell.api.root  # noqa: F401
import ifcopenshell.guid
import ifcopenshell.api.group  # noqa: F401
import ifcopenshell.api.pset  # noqa: F401
import ifcopenshell.api.structural  # noqa: F401
import ifcopenshell.util.element

TAG = "ArqSynth BIM"
SETTINGS_PSET = "ArqSynth_Estrutura"


class StructuralMixin:
    def _graph_context(self):
        for ctx in self.file.by_type("IfcGeometricRepresentationSubContext"):
            if ctx.ContextIdentifier == "Reference" and ctx.TargetView == "GRAPH_VIEW":
                return ctx
        parent = self.body.ParentContext
        return api.context.add_context(self.file, context_type="Model", context_identifier="Reference",
                                       target_view="GRAPH_VIEW", parent=parent)

    def analysis_models(self):
        return [m for m in self.file.by_type("IfcStructuralAnalysisModel") if (m.Description or "") == TAG]

    def _remove_analysis_model(self):
        self._remove_results()                              # (0.221: its results go with it)
        self._remove_loads()
        for model in self.analysis_models():
            items = [obj for rel in (model.IsGroupedBy or ()) for obj in rel.RelatedObjects]
            api.structural.remove_structural_analysis_model(self.file, structural_analysis_model=model)
            for obj in items:
                if obj.is_a("IfcStructuralItem"):
                    api.root.remove_product(self.file, product=obj)

    # ------------------------------------------------------------ settings and loads (0.164)

    def structural_settings(self):
        """The project's structural settings (core.actions.Settings), kept in its building's ArqSynth_Estrutura."""
        from ..core import actions
        settings = actions.Settings()
        buildings = self.file.by_type("IfcBuilding")
        if not buildings:
            return settings
        stored = ifcopenshell.util.element.get_psets(buildings[0]).get(SETTINGS_PSET, {})
        for name, value in stored.items():
            if name == "id" or not hasattr(settings, name):
                continue
            current = getattr(settings, name)
            try:
                setattr(settings, name, type(current)(value))
            except (TypeError, ValueError):
                pass
        settings.terrain = actions.TERRAIN_OLD.get(settings.terrain, settings.terrain)    # (0.219: the NA's four)
        return settings

    def set_structural_settings(self, settings):
        import dataclasses
        buildings = self.file.by_type("IfcBuilding")
        if not buildings:
            return
        b = buildings[0]
        existing = ifcopenshell.util.element.get_psets(b).get(SETTINGS_PSET)
        pset = self.file.by_id(existing["id"]) if existing else api.pset.add_pset(self.file, product=b,
                                                                                  name=SETTINGS_PSET)
        values = {k: (float(v) if isinstance(v, (int, float)) else str(v))
                  for k, v in dataclasses.asdict(settings).items()}
        api.pset.edit_pset(self.file, pset=pset, properties=values)

    def _remove_loads(self):
        for group in [g for g in self.file.by_type("IfcStructuralLoadGroup") if (g.Description or "") == TAG]:
            actions = [o for rel in (group.IsGroupedBy or ()) for o in rel.RelatedObjects
                       if o.is_a("IfcStructuralAction")]
            for action in actions:
                api.root.remove_product(self.file, product=action)
            api.structural.remove_structural_load_group(self.file, load_group=group)

    def write_loads(self, loads):
        """The gravity load cases of the analytical model — G (permanent: the slabs' and the members' own weight,
        finishes, partitions) and Q (imposed) — as IfcStructuralLoadGroup cases with their actions: on each slab a
        planar force, on each member its own weight as a linear force (N/m², N/m: SI, the project gives no force
        unit). loads: model.structure_loads.BuildingActions."""
        f = self.file
        self._remove_loads()
        models = self.analysis_models()
        if not models:
            return []
        analysis = models[0]
        items = [o for rel in (analysis.IsGroupedBy or ()) for o in rel.RelatedObjects]
        panels = {o.Name: o for o in items if o.is_a("IfcStructuralSurfaceMember")}
        members = {o.Name: o for o in items if o.is_a("IfcStructuralCurveMember")}
        cases = []
        for name, action_type, source, per_panel, per_member in (
                ("G", "PERMANENT_G", "DEAD_LOAD_G", loads.panel_g, loads.member_g),
                ("Q", "VARIABLE_Q", "LIVE_LOAD_Q", loads.panel_q, {})):
            case = api.structural.add_structural_load_case(f, name=name, action_type=action_type,
                                                           action_source=source)
            case.Description = TAG
            for guid, value in per_panel.items():
                panel = panels.get(guid)
                if panel is None or not value:
                    continue
                load = api.structural.add_structural_load(f, name="{} {:.2f} kN/m²".format(name, value),
                                                          ifc_class="IfcStructuralLoadPlanarForce")
                load.PlanarForceZ = -float(value) * 1000.0
                act = api.structural.add_structural_activity(f, applied_load=load, structural_member=panel,
                                                             ifc_class="IfcStructuralPlanarAction")
                api.group.assign_group(f, products=[act], group=case)
            for mid, value in per_member.items():
                member = members.get(mid)
                if member is None or not value:
                    continue
                load = api.structural.add_structural_load(f, name="{} {:.2f} kN/m".format(name, value),
                                                          ifc_class="IfcStructuralLoadLinearForce")
                load.LinearForceZ = -float(value) * 1000.0
                act = api.structural.add_structural_activity(f, applied_load=load, structural_member=member,
                                                             ifc_class="IfcStructuralCurveAction",
                                                             predefined_type="CONST")
                api.group.assign_group(f, products=[act], group=case)
            cases.append(case)
        analysis.LoadedBy = cases
        return cases

    def _remove_results(self):
        for group in [g for g in self.file.by_type("IfcStructuralResultGroup") if (g.Description or "") == TAG]:
            for obj in [o for rel in (group.IsGroupedBy or ()) for o in rel.RelatedObjects]:
                if obj.is_a("IfcStructuralReaction"):
                    api.root.remove_product(self.file, product=obj)
            api.root.remove_product(self.file, product=group)
        for group in [g for g in self.file.by_type("IfcStructuralLoadGroup")
                      if (g.Description or "") == TAG and g.PredefinedType == "LOAD_COMBINATION"]:
            for rel in list(getattr(group, "IsGroupedBy", None) or ()):
                self.file.remove(rel)
            api.root.remove_product(self.file, product=group)

    def write_results(self, analysis):
        """(0.220-0.221) The analysis's results in the IFC (the old ones replaced): its first ULS combination as an
        IfcStructuralLoadGroup LOAD_COMBINATION of the cases G and Q (their factors by IfcRelAssignsToGroupByFactor);
        an IfcStructuralResultGroup for it (first order, linear), the analysis model's result: the supports' reactions
        (IfcStructuralPointReaction, single forces) and each member's bending moments along it
        (IfcStructuralCurveReaction DISCRETE: a load configuration of moments at their lengths) — N, N·m (SI).
        analysis: model.structure_analysis.Analysis. Returns the result group, or None (no analysis model)."""
        f = self.file
        self._remove_results()
        models = self.analysis_models()
        if not models or analysis is None or analysis.error:
            return None
        model = models[0]
        items = [o for rel in (model.IsGroupedBy or ()) for o in rel.RelatedObjects]
        nodes = {o.Name: o for o in items if o.is_a("IfcStructuralPointConnection")}
        members = {o.Name: o for o in items if o.is_a("IfcStructuralCurveMember")}
        cases = {c.Name: c for c in (model.LoadedBy or ())}
        combo = api.root.create_entity(f, ifc_class="IfcStructuralLoadGroup", name=analysis.diagram_combo or "ELU",
                                       predefined_type="LOAD_COMBINATION")
        combo.Description, combo.ActionType, combo.ActionSource = TAG, "NOTDEFINED", "NOTDEFINED"
        for name, factor in (("G", 1.35), ("Q", 1.50)):
            if name in cases:
                f.createIfcRelAssignsToGroupByFactor(ifcopenshell.guid.new(), None, None, None, [cases[name]], None,
                                                     combo, factor)
        group = api.root.create_entity(f, ifc_class="IfcStructuralResultGroup",
                                       name="{} — {}".format(analysis.diagram_combo or "ELU", TAG))
        group.Description, group.TheoryType, group.ResultForLoadGroup, group.IsLinear = \
            TAG, "FIRST_ORDER_THEORY", combo, True
        made = []
        for k, r in analysis.reactions.items():                 # (the supports: node index -> 6 forces, kN / kNm)
            node = nodes.get("N{}".format(int(k) + 1))
            if node is None:
                continue
            load = api.structural.add_structural_load(f, name="R{}".format(int(k) + 1),
                                                      ifc_class="IfcStructuralLoadSingleForce")
            load.ForceX, load.ForceY, load.ForceZ, load.MomentX, load.MomentY, load.MomentZ = \
                (float(v) * 1000.0 for v in r)
            made.append(api.structural.add_structural_activity(f, applied_load=load, structural_member=node,
                                                               ifc_class="IfcStructuralPointReaction"))
        for mid, (p1, p2, _z, moments) in analysis.diagrams.items():
            member = members.get(mid)
            if member is None:
                continue
            length = float(np.linalg.norm(np.asarray(p2, dtype=float) - np.asarray(p1, dtype=float)))
            values = []
            for m in moments:
                single = f.createIfcStructuralLoadSingleForce(None, None, None, None, None, float(m) * 1000.0, None)
                values.append(single)
            spots = [[float(length * i / max(len(moments) - 1, 1) / self.unit_scale)] for i in range(len(moments))]
            configuration = f.createIfcStructuralLoadConfiguration("M " + mid, values, spots)
            made.append(api.structural.add_structural_activity(f, applied_load=configuration, structural_member=member,
                                                               ifc_class="IfcStructuralCurveReaction",
                                                               predefined_type="DISCRETE"))
        if made:
            api.group.assign_group(f, products=made, group=group)
        model.HasResults = [group]
        return group

    def write_analysis_model(self, model, name="Modelo analítico"):
        """The core.structural.AnalyticalModel in the IFC (the old one replaced). Returns the IfcStructuralAnalysisModel."""
        f, u = self.file, 1.0 / self.unit_scale
        self._remove_analysis_model()
        if not model.members and not model.panels and not getattr(model, "walls", ()):
            return None
        ctx = self._graph_context()
        shift = np.asarray(self.origin, dtype=float)

        def point(p):
            q = np.asarray(p, dtype=float) + shift
            return f.createIfcCartesianPoint(tuple(float(c * u) for c in q))

        analysis = api.structural.add_structural_analysis_model(f)
        api.structural.edit_structural_analysis_model(f, structural_analysis_model=analysis, attributes={
            "Name": name, "Description": TAG, "PredefinedType": "LOADING_3D"})
        items, vertices, nodes = [], [], []
        for k, p in enumerate(model.nodes):
            vertex = f.createIfcVertexPoint(point(p))
            node = api.root.create_entity(f, ifc_class="IfcStructuralPointConnection", name="N{}".format(k + 1))
            api.geometry.edit_object_placement(f, product=node)
            api.geometry.assign_representation(f, product=node, representation=f.createIfcTopologyRepresentation(
                ctx, "Reference", "Vertex", [vertex]))
            vertices.append(vertex)
            nodes.append(node)
            items.append(node)
            kind = model.supports.get(k)
            if kind is not None:
                cond = api.structural.add_structural_boundary_condition(f, name=kind, connection=node)
                fixed = {"type": "IfcBoolean", "value": True}
                free = {"type": "IfcBoolean", "value": False}
                attrs = {"TranslationalStiffness" + a: fixed for a in "XYZ"}
                attrs.update({"RotationalStiffness" + a: fixed if kind == "fixed" else free for a in "XYZ"})
                api.structural.edit_structural_boundary_condition(f, condition=cond, attributes=attrs)
        for m in model.members:
            member = api.root.create_entity(f, ifc_class="IfcStructuralCurveMember", name=m.id,
                                            predefined_type="RIGID_JOINED_MEMBER")
            axis = (1.0, 0.0, 0.0) if m.kind == "column" else (0.0, 0.0, 1.0)     # (its section's local z)
            member.Axis = f.createIfcDirection(axis)
            api.geometry.edit_object_placement(f, product=member)
            edge = f.createIfcEdge(vertices[m.n1], vertices[m.n2])
            api.geometry.assign_representation(f, product=member, representation=f.createIfcTopologyRepresentation(
                ctx, "Reference", "Edge", [edge]))
            for n in (m.n1, m.n2):
                api.structural.add_structural_member_connection(f, relating_structural_member=member,
                                                                related_structural_connection=nodes[n])
            physical = self.by_guid(m.guid)
            if physical is not None:
                api.structural.assign_product(f, relating_product=physical, related_object=member)
                material = ifcopenshell.util.element.get_material(physical, should_skip_usage=True)
                if material is not None and material.is_a("IfcMaterialProfileSet") and material.MaterialProfiles:
                    mat = material.MaterialProfiles[0].Material
                    if mat is not None:
                        api.material.assign_material(f, products=[member], type="IfcMaterial", material=mat)
            items.append(member)
        for p in model.panels:
            panel = api.root.create_entity(f, ifc_class="IfcStructuralSurfaceMember", name=p.guid,
                                           predefined_type="BENDING_ELEMENT")
            panel.Thickness = float(p.thickness * u)
            api.geometry.edit_object_placement(f, product=panel)
            loop = f.createIfcPolyLoop([point((x, y, p.level)) for x, y in p.outline])
            plane = f.createIfcPlane(f.createIfcAxis2Placement3D(point((0.0, 0.0, p.level)), None, None))
            face = f.createIfcFaceSurface([f.createIfcFaceOuterBound(loop, True)], plane, True)
            api.geometry.assign_representation(f, product=panel, representation=f.createIfcTopologyRepresentation(
                ctx, "Reference", "Face", [face]))
            physical = self.by_guid(p.guid)
            if physical is not None:
                api.structural.assign_product(f, relating_product=physical, related_object=panel)
            items.append(panel)
        for w in getattr(model, "walls", ()):               # (0.335) the load-bearing walls: their mid planes
            wall = api.root.create_entity(f, ifc_class="IfcStructuralSurfaceMember", name=w.guid,
                                          predefined_type="SHELL")
            wall.Thickness = float(w.t * u)
            api.geometry.edit_object_placement(f, product=wall)
            corners = [(*w.start, w.base), (*w.end, w.base), (*w.end, w.top), (*w.start, w.top)]
            along = np.subtract(w.end, w.start) / max(w.length, 1e-9)
            loop = f.createIfcPolyLoop([point(c) for c in corners])
            plane = f.createIfcPlane(f.createIfcAxis2Placement3D(
                point(corners[0]), f.createIfcDirection((float(-along[1]), float(along[0]), 0.0)),
                f.createIfcDirection((float(along[0]), float(along[1]), 0.0))))
            face = f.createIfcFaceSurface([f.createIfcFaceOuterBound(loop, True)], plane, True)
            api.geometry.assign_representation(f, product=wall, representation=f.createIfcTopologyRepresentation(
                ctx, "Reference", "Face", [face]))
            physical = self.by_guid(w.guid)
            if physical is not None:
                api.structural.assign_product(f, relating_product=physical, related_object=wall)
            items.append(wall)
        api.structural.assign_structural_analysis_model(f, products=items, structural_analysis_model=analysis)
        buildings = f.by_type("IfcBuilding")
        if buildings:
            api.structural.assign_to_building(f, structural_analysis_model=analysis, building=buildings[0])
        return analysis

    def analytical_lines(self):
        """The analytical model as drawn: ([(kind "column" | "beam", a (3,), b (3,))], [(node (3,), "fixed" |
        "pinned")], [panel outlines (N, 3)]) — program coordinates."""
        s, shift = self.unit_scale, np.asarray(self.origin, dtype=float)
        lines, supports, panels = [], [], []
        for model in self.analysis_models():
            for rel in model.IsGroupedBy or ():
                for obj in rel.RelatedObjects:
                    rep = next((r for r in (obj.Representation.Representations if obj.Representation else ())
                                if r.RepresentationIdentifier == "Reference"), None)
                    if rep is None or not rep.Items:
                        continue
                    item = rep.Items[0]
                    if obj.is_a("IfcStructuralCurveMember") and item.is_a("IfcEdge"):
                        a = np.array(item.EdgeStart.VertexGeometry.Coordinates) * s - shift
                        b = np.array(item.EdgeEnd.VertexGeometry.Coordinates) * s - shift
                        kind = "column" if abs(a[2] - b[2]) > max(abs(a[0] - b[0]), abs(a[1] - b[1])) else "beam"
                        lines.append((kind, a, b))
                    elif obj.is_a("IfcStructuralPointConnection") and obj.AppliedCondition is not None:
                        p = np.array(item.VertexGeometry.Coordinates) * s - shift
                        rot = obj.AppliedCondition.RotationalStiffnessX
                        fixed = bool(getattr(rot, "wrappedValue", rot)) if rot is not None else False
                        supports.append((p, "fixed" if fixed else "pinned"))
                    elif obj.is_a("IfcStructuralSurfaceMember") and item.is_a("IfcFaceSurface"):
                        loop = item.Bounds[0].Bound
                        panels.append(np.array([c.Coordinates for c in loop.Polygon]) * s - shift)
        return lines, supports, panels
