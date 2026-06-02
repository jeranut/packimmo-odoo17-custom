# -*- coding: utf-8 -*-
from odoo import fields, models


class PropertyDetails(models.Model):
    _inherit = "property.details"

    syndic_active = fields.Boolean(
        string="Inclus dans le syndic",
        default=True,
        help="Décochez si ce bien ne doit pas être pris en compte dans la gestion syndic.",
    )
