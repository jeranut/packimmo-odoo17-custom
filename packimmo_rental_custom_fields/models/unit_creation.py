from odoo import _, models
from odoo.exceptions import ValidationError


class UnitCreation(models.TransientModel):
    _inherit = "unit.creation"

    def action_create_property_unit(self):
        self.ensure_one()

        if self.total_floors <= 0:
            self.total_floors = 1

        if self.env.context.get("unit_from") == "project":
            requested_unit_count = self.total_floors * self.units_per_floor
            project_id = self.env.context.get("active_id")
            existing_unit_count = self.env["property.details"].search_count(
                [
                    ("property_project_id", "=", project_id),
                    ("subproject_id", "=", False),
                ]
            )

            if requested_unit_count + existing_unit_count > 1:
                raise ValidationError(
                    _(
                        "Pour créer plus d'un bien ou lot, il faut créer un "
                        "sous-projet et créer les biens dans ce sous-projet."
                    )
                )

        return super().action_create_property_unit()
