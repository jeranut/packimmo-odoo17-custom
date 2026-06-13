import json

from odoo import http
from odoo.http import request


class PackimmoMapAnnotationsController(http.Controller):

    def _scope_domain(self, project_id=None, subproject_id=None):
        domain = [("active", "=", True)]
        if subproject_id:
            domain.append(("subproject_id", "=", int(subproject_id)))
        elif project_id:
            domain.append(("project_id", "=", int(project_id)))
        else:
            domain.append(("id", "=", 0))
        return domain

    @http.route("/packimmo/map-annotations/data", type="json", auth="user", website=True)
    def map_annotations_data(self, project_id=None, subproject_id=None, **kw):
        annotations = request.env["property.map.annotation"].sudo().search(
            self._scope_domain(project_id, subproject_id)
        )
        zones = request.env["property.map.interest.zone"].sudo().search(
            self._scope_domain(project_id, subproject_id)
        )
        return {
            "annotations": [a.to_map_dict() for a in annotations],
            "zones": [z.to_map_dict() for z in zones],
        }

    @http.route("/packimmo/map-annotations/save", type="json", auth="user", website=True)
    def map_annotation_save(self, **kw):
        vals = {
            "name": kw.get("name") or "Légende",
            "description": kw.get("description") or False,
            "project_id": kw.get("project_id") or False,
            "subproject_id": kw.get("subproject_id") or False,
            "target_lat": kw.get("target_lat"),
            "target_lng": kw.get("target_lng"),
            "label_lat": kw.get("label_lat"),
            "label_lng": kw.get("label_lng"),
            "color": kw.get("color") or "#111827",
            "icon": kw.get("icon") or "info",
        }
        rec = request.env["property.map.annotation"].sudo().create(vals)
        return {"ok": True, "record": rec.to_map_dict()}

    @http.route("/packimmo/map-interest-zones/save", type="json", auth="user", website=True)
    def map_interest_zone_save(self, **kw):
        polygon = kw.get("polygon") or []
        vals = {
            "name": kw.get("name") or "Zone d'intérêt",
            "description": kw.get("description") or False,
            "project_id": kw.get("project_id") or False,
            "subproject_id": kw.get("subproject_id") or False,
            "zone_type": kw.get("zone_type") or "other",
            "polygon_json": json.dumps(polygon),
            "color": kw.get("color") or "#22c55e",
            "opacity": kw.get("opacity") or 0.25,
        }
        rec = request.env["property.map.interest.zone"].sudo().create(vals)
        return {"ok": True, "record": rec.to_map_dict()}

    @http.route("/packimmo/map-annotation/delete", type="json", auth="user", website=True)
    def map_annotation_delete(self, model=None, record_id=None, **kw):
        if model not in ["property.map.annotation", "property.map.interest.zone"] or not record_id:
            return {"ok": False, "error": "Paramètres invalides"}
        rec = request.env[model].sudo().browse(int(record_id))
        if rec.exists():
            rec.unlink()
        return {"ok": True}
