import json

from odoo import http
from odoo.http import request


class PackimmoMapAnnotationsController(http.Controller):

    def _int(self, value, default=False):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _float(self, value, default=False):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _json(self, value, default=None):
        if value is None:
            return default
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return default
        return value

    def _is_public(self):
        return hasattr(request.env.user, "_is_public") and request.env.user._is_public()

    def _scope_domain(self, project_id=None, subproject_id=None):
        domain = [("active", "=", True)]
        if self._is_public():
            domain.append(("website_published", "=", True))
        if subproject_id:
            domain.append(("subproject_id", "=", self._int(subproject_id)))
        elif project_id:
            project_id = self._int(project_id)
            domain.extend([
                "|",
                ("project_id", "=", project_id),
                ("subproject_id.property_project_id", "=", project_id),
            ])
        else:
            domain.append(("id", "=", 0))
        return domain

    def _normalize_points(self, points):
        if not isinstance(points, list):
            return []
        normalized = []
        for point in points:
            if isinstance(point, dict):
                lat = self._float(point.get("lat"), None)
                lng = self._float(point.get("lng"), None)
            elif isinstance(point, (list, tuple)) and len(point) == 2:
                lat = self._float(point[0], None)
                lng = self._float(point[1], None)
            else:
                continue
            if lat is None or lng is None:
                continue
            normalized.append([lng, lat])
        return normalized

    def _polygon_coordinates(self, geometry):
        if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
            return []
        coordinates = geometry.get("coordinates") or []
        if not coordinates or not isinstance(coordinates[0], list):
            return []
        normalized = []
        for point in coordinates[0]:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            lng = self._float(point[0], None)
            lat = self._float(point[1], None)
            if lng is not None and lat is not None:
                normalized.append([lng, lat])
        return normalized

    def _geometry_centroid(self, geometry):
        if not isinstance(geometry, dict):
            return None
        gtype = geometry.get("type")
        coords = geometry.get("coordinates")
        if gtype == "Point" and isinstance(coords, list) and len(coords) >= 2:
            return [coords[1], coords[0]]
        if gtype == "LineString" and isinstance(coords, list) and coords:
            point = coords[-1]
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                return [point[1], point[0]]
        if gtype == "Polygon" and isinstance(coords, list) and coords and isinstance(coords[0], list):
            ring = coords[0]
            valid = [
                [self._float(point[0], None), self._float(point[1], None)]
                for point in ring
                if isinstance(point, (list, tuple)) and len(point) >= 2
            ]
            valid = [point for point in valid if point[0] is not None and point[1] is not None]
            if not valid:
                return None
            lat = sum(point[1] for point in valid) / len(valid)
            lng = sum(point[0] for point in valid) / len(valid)
            return [lat, lng]
        return None

    @http.route("/packimmo/map-annotations/data", type="json", auth="public", website=True)
    def map_annotations_data(self, project_id=None, subproject_id=None, **kw):
        annotations = request.env["property.map.annotation"].sudo().search(
            self._scope_domain(project_id, subproject_id)
        )
        zones = request.env["property.map.interest.zone"].sudo().search(
            self._scope_domain(project_id, subproject_id)
        )
        return {
            "ok": True,
            "annotations": [a.to_map_dict() for a in annotations],
            "zones": [z.to_map_dict() for z in zones],
        }

    @http.route("/packimmo/map-annotations/save", type="json", auth="user", website=True)
    def map_annotation_save(self, **kw):
        project_id = self._int(kw.get("project_id"))
        subproject_id = self._int(kw.get("subproject_id"))
        if not project_id and not subproject_id:
            return {"ok": False, "error": "project_id ou subproject_id requis"}

        annotation = self._json(kw.get("annotation"), None)
        geometry = self._json(kw.get("geometry"), None)
        polygon = self._json(kw.get("polygon"), None)
        if polygon:
            points = self._normalize_points(polygon)
            if len(points) == 1:
                geometry = {"type": "Point", "coordinates": points[0]}
            elif len(points) > 1:
                geometry = {"type": "Polygon", "coordinates": [points]}

        if geometry and not isinstance(geometry, dict):
            geometry = None

        target_lat = self._float(kw.get("target_lat"), None)
        target_lng = self._float(kw.get("target_lng"), None)
        label_lat = self._float(kw.get("label_lat"), None)
        label_lng = self._float(kw.get("label_lng"), None)
        color = kw.get("color") or "#111827"
        text_color = kw.get("text_color") or color

        if isinstance(annotation, dict) and annotation.get("type") == "legend":
            start = annotation.get("start") or []
            end = annotation.get("end") or []
            style = annotation.get("style") or {}
            if (
                not isinstance(start, (list, tuple))
                or not isinstance(end, (list, tuple))
                or not isinstance(style, dict)
                or len(start) < 2
                or len(end) < 2
            ):
                return {"ok": False, "error": "Coordonnées de la légende invalides"}
            label_lat = self._float(start[0], None)
            label_lng = self._float(start[1], None)
            target_lat = self._float(end[0], None)
            target_lng = self._float(end[1], None)
            color = style.get("color") or color
            text_color = style.get("text_color") or text_color
            annotation = {
                "type": "legend",
                "text": annotation.get("text") or kw.get("name") or "Légende",
                "start": [label_lat, label_lng],
                "end": [target_lat, target_lng],
                "style": {
                    "color": color,
                    "text_color": text_color,
                    "weight": self._float(style.get("weight"), 3),
                },
            }
        elif annotation:
            annotation = None

        if geometry and (target_lat is None or target_lng is None or label_lat is None or label_lng is None):
            centroid = self._geometry_centroid(geometry)
            if centroid:
                target_lat = target_lat if target_lat is not None else centroid[0]
                target_lng = target_lng if target_lng is not None else centroid[1]
                label_lat = label_lat if label_lat is not None else centroid[0]
                label_lng = label_lng if label_lng is not None else centroid[1]

        if target_lat is None or target_lng is None or label_lat is None or label_lng is None:
            return {"ok": False, "error": "Coordonnées de la légende invalides"}

        vals = {
            "name": (annotation or {}).get("text") or kw.get("name") or "Légende",
            "description": kw.get("description") or False,
            "project_id": project_id or False,
            "subproject_id": subproject_id or False,
            "target_lat": target_lat,
            "target_lng": target_lng,
            "label_lat": label_lat,
            "label_lng": label_lng,
            "color": color,
            "text_color": text_color,
            "icon": kw.get("icon") or "info",
        }
        if annotation:
            vals["geometry_json"] = json.dumps(annotation)
        elif geometry:
            vals["geometry_json"] = json.dumps(geometry)

        rec = request.env["property.map.annotation"].sudo().create(vals)
        return {"ok": True, "record": rec.to_map_dict()}

    @http.route("/packimmo/map-interest-zones/save", type="json", auth="user", website=True)
    def map_interest_zone_save(self, **kw):
        project_id = self._int(kw.get("project_id"))
        subproject_id = self._int(kw.get("subproject_id"))
        if not project_id and not subproject_id:
            return {"ok": False, "error": "project_id ou subproject_id requis"}

        geometry = self._json(kw.get("geometry"), None)
        polygon = self._json(kw.get("polygon"), None)
        if polygon:
            points = self._normalize_points(polygon)
            if len(points) > 2:
                geometry = {"type": "Polygon", "coordinates": [points]}

        polygon_json = False
        if geometry and geometry.get("type") == "Point":
            coords = geometry.get("coordinates") or []
            if len(coords) >= 2:
                lng = self._float(coords[0], None)
                lat = self._float(coords[1], None)
                if lat is not None and lng is not None:
                    polygon_json = json.dumps([{"lng": lng, "lat": lat}])
        elif geometry and geometry.get("type") == "Polygon":
            coords = self._polygon_coordinates(geometry)
            if len(coords) > 2:
                polygon_json = json.dumps([{"lng": lng, "lat": lat} for [lng, lat] in coords])
        elif polygon:
            polygon_json = json.dumps(polygon)

        if not polygon_json:
            return {"ok": False, "error": "Position ou polygone invalide"}

        vals = {
            "name": kw.get("name") or "Zone d'intérêt",
            "description": kw.get("description") or False,
            "project_id": project_id or False,
            "subproject_id": subproject_id or False,
            "zone_type": kw.get("zone_type") or "other",
            "polygon_json": polygon_json,
            "color": kw.get("color") or "#22c55e",
            "text_color": kw.get("text_color") or kw.get("color") or "#111827",
            "opacity": self._float(kw.get("opacity"), 0.25),
        }

        rec = request.env["property.map.interest.zone"].sudo().create(vals)
        return {"ok": True, "record": rec.to_map_dict()}

    @http.route("/packimmo/map-annotation/delete", type="json", auth="user", website=True)
    def map_annotation_delete(self, model=None, record_id=None, **kw):
        if model not in ["property.map.annotation", "property.map.interest.zone"] or not record_id:
            return {"ok": False, "error": "Paramètres invalides"}
        rec = request.env[model].sudo().browse(self._int(record_id))
        if rec.exists():
            rec.unlink()
        return {"ok": True}
