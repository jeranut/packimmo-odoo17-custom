from odoo import api, fields, models


class SubprojectCreation(models.TransientModel):
    _inherit = "subproject.creation"

    project_sequence = fields.Char(
        string="Code",
        required=False,
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project = self.env["property.project"].browse(self.env.context.get("active_id"))
        if project.exists():
            res["project_sequence"] = project.project_sequence
        return res

    def create_sub_project(self):
        for wizard in self:
            project = self.env["property.project"].browse(
                wizard.env.context.get("active_id")
            )
            if project.exists():
                wizard.project_sequence = project.project_sequence
        return super().create_sub_project()
