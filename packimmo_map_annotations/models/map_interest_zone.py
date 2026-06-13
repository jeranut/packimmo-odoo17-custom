from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PropertyMapInterestZone(models.Model):
    _name = "property.map.interest.zone"
    _description = "Zone d'intérêt de carte Packimmo"
    _order = "sequence, id"

    name = fields.Char("Nom", required=True)
    description = fields.Text("Description")
    project_id = fields.Many2one("property.project", string="Projet", ondelete="cascade")
    subproject_id = fields.Many2one("property.sub.project", string="Sous-projet / Phase", ondelete="cascade")

    zone_type = fields.Selection([
        ("green", "Zone verte"),
        ("leisure", "Loisirs"),
        ("commercial", "Zone commerciale"),
        ("parking", "Parking"),
        ("access", "Accès"),
        ("reserve", "Réserve"),
        ("water", "Lac / bassin"),
        ("other", "Autre"),
    ], string="Type", default="other")
    polygon_json = fields.Text("Polygone JSON", required=True)
    color = fields.Char("Couleur", default="#22c55e")
    opacity = fields.Float("Opacité", default=0.25)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.constrains("project_id", "subproject_id")
    def _check_scope(self):
        for rec in self:
            if not rec.project_id and not rec.subproject_id:
                raise ValidationError("Une zone d'intérêt doit être liée à un projet ou à un sous-projet.")

    def to_map_dict(self):
        self.ensure_one()
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "zone_type": self.zone_type or "other",
            "polygon_json": self.polygon_json or "[]",
            "color": self.color or "#22c55e",
            "opacity": self.opacity if self.opacity is not False else 0.25,
        }
