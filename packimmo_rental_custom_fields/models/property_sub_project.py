from odoo import api, fields, models


class PropertySubProject(models.Model):
    _inherit = "property.sub.project"
    _order = "date_of_project desc, id desc"

    property_type = fields.Selection(
        [
            ("residential", "Résidentielle"),
            ("commercial", "Commerciale"),
            ("land", "Terrain"),
        ],
        string="Property Type",
    )

    project_sequence = fields.Char(
        readonly=True,
        required=False,
        copy=False,
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        if "property_type" in res and "selection" in res["property_type"]:
            res["property_type"]["selection"] = [
                item for item in res["property_type"]["selection"]
                if item[0] != "industrial"
            ]
        return res

    def _get_address_vals_from_project(self, project):
        if not project:
            return {}

        return {
            "region_id": project.region_id.id if project.region_id else False,
            "street": project.street or False,
            "street2": project.street2 or False,
            "city_id": project.city_id.id if project.city_id else False,
            "state_id": project.state_id.id if project.state_id else False,
            "zip": project.zip or False,
            "country_id": project.country_id.id if project.country_id else False,
        }

    @api.onchange("property_project_id")
    def _onchange_property_project_id_copy_address(self):
        for rec in self:
            vals = rec._get_address_vals_from_project(rec.property_project_id)
            for field_name, value in vals.items():
                rec[field_name] = value
            rec.project_sequence = rec.property_project_id.project_sequence

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            project_id = vals.get("property_project_id")
            if project_id:
                project = self.env["property.project"].browse(project_id)
                vals.update(self._get_address_vals_from_project(project))
                vals["project_sequence"] = project.project_sequence

        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)

        if "property_project_id" in vals and vals.get("property_project_id"):
            project = self.env["property.project"].browse(vals["property_project_id"])
            vals.update(self._get_address_vals_from_project(project))
            vals["project_sequence"] = project.project_sequence

        return super().write(vals)
