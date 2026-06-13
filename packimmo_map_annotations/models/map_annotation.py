from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PropertyMapAnnotation(models.Model):
    _name = "property.map.annotation"
    _description = "Légende de carte Packimmo"
    _order = "sequence, id"

    name = fields.Char("Titre", required=True)
    description = fields.Text("Description")
    project_id = fields.Many2one("property.project", string="Projet", ondelete="cascade")
    subproject_id = fields.Many2one("property.sub.project", string="Sous-projet / Phase", ondelete="cascade")

    target_lat = fields.Float("Point visé - Latitude", digits=(16, 8), required=True)
    target_lng = fields.Float("Point visé - Longitude", digits=(16, 8), required=True)
    label_lat = fields.Float("Position texte - Latitude", digits=(16, 8), required=True)
    label_lng = fields.Float("Position texte - Longitude", digits=(16, 8), required=True)

    color = fields.Char("Couleur", default="#111827")
    icon = fields.Selection([
        ("info", "Information"),
        ("entrance", "Entrée"),
        ("club", "Club / Loisirs"),
        ("parking", "Parking"),
        ("lake", "Lac"),
        ("park", "Parc"),
        ("security", "Sécurité"),
        ("commercial", "Zone commerciale"),
        ("road", "Route"),
        ("beach", "Plage"),
    ], string="Icône", default="info")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.constrains("project_id", "subproject_id")
    def _check_scope(self):
        for rec in self:
            if not rec.project_id and not rec.subproject_id:
                raise ValidationError("Une légende doit être liée à un projet ou à un sous-projet.")

    def to_map_dict(self):
        self.ensure_one()
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "target": {"lat": self.target_lat, "lng": self.target_lng},
            "label": {"lat": self.label_lat, "lng": self.label_lng},
            "color": self.color or "#111827",
            "icon": self.icon or "info",
        }
