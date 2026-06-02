from odoo import models


class UnitCreation(models.TransientModel):
    _inherit = "unit.creation"

    def action_create_property_unit(self):
        if self.total_floors <= 0:
            self.total_floors = 1

        return super().action_create_property_unit()
