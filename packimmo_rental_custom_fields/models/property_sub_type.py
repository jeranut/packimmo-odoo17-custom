from odoo import fields, models


class PropertySubType(models.Model):
    _inherit = "property.sub.type"

    category = fields.Selection(
        [
            ("commune", "Commune"),
            ("independant", "Indépendant"),
            ("morcellement", "Morcellement"),
            ("commercial", "Commercial"),
            ("bureaux", "Bureaux"),
            ("stockage", "Stockage"),
        ],
        string="Catégorie",
    )