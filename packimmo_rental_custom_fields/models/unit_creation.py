from odoo import _, models
from odoo.exceptions import ValidationError


class UnitCreation(models.TransientModel):
    _inherit = "unit.creation"

    def action_create_property_unit(self):
        self.ensure_one()

        unit_from = self.env.context.get("unit_from")
        active_id = self.env.context.get("active_id")

        is_land_project = False

        if unit_from == "project" and active_id:
            project = self.env["property.project"].browse(active_id)
            is_land_project = project.exists() and project.property_type == "land"

        elif unit_from == "sub_project" and active_id:
            project = self.env["property.sub.project"].browse(active_id)
            is_land_project = project.exists() and project.property_type == "land"

        if is_land_project:
            self = self.with_context(default_type="land", default_property_type="land")

        if not is_land_project and self.total_floors <= 0:
            self.total_floors = 1

        if unit_from == "project":
            requested_unit_count = self.total_floors * self.units_per_floor

            if is_land_project:
                requested_unit_count = self.units_per_floor

            existing_unit_count = self.env["property.details"].search_count(
                [
                    ("property_project_id", "=", active_id),
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

        return super(UnitCreation, self).action_create_property_unit()