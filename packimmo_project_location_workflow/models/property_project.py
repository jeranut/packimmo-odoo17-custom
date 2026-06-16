# -*- coding: utf-8 -*-

from odoo import models


class PropertyProject(models.Model):
    _inherit = "property.project"

    def _ensure_location_property_details(self):
        for project in self.sudo():
            self.env["property.details"].sudo().search([
                ("property_project_id", "=", project.id),
                ("sale_lease", "=", "for_tenancy"),
                ("stage", "=", "available"),
            ])._sync_location_project_task()

    def action_packimmo_after_location_create(self):
        self.ensure_one()
        self._ensure_location_property_details()
        return self.env["project.task"].action_open_location_kanban()
