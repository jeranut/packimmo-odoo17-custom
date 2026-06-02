from odoo import fields, models


class PropertyAreaType(models.Model):
    _inherit = "property.area.type"

    type = fields.Selection(
        selection_add=[
            ("garage", "Garage"),
        ],
        ondelete={
            "garage": "cascade",
        },
    )
