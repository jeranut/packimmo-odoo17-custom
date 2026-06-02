# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class PropertyUnitMapImportWizard(models.TransientModel):
    _name = 'property.unit.map.import.wizard'
    _description = 'Import Unit Map Image Wizard'

    project_id = fields.Many2one('property.project', string='Project')
    map_image = fields.Binary(string='Map Image', required=True, attachment=True)
    map_image_name = fields.Char(string='Filename')
    total_floors = fields.Integer(string='Total Floors')
    units_per_floor = fields.Integer(string='Units per Floor')
    subproject_id = fields.Many2one(
        'property.sub.project',
        string='Sub Project'
    )

    def action_import_and_open_map(self):
        self.ensure_one()

        if self.subproject_id:
            self.subproject_id.write({
                'unit_map_image': self.map_image,
                'unit_map_image_name': self.map_image_name,
            })
            self.subproject_id.action_prepare_unit_map_lines()

            return {
                'type': 'ir.actions.act_url',
                'url': '/property/subproject/unit-map/designer/%s' % self.subproject_id.id,
                'target': 'self',
            }

        if self.project_id:
            self.project_id.write({
                'unit_map_image': self.map_image,
                'unit_map_image_name': self.map_image_name,
            })
            self.project_id.action_prepare_unit_map_lines()

            return {
                'type': 'ir.actions.act_url',
                'url': '/property/unit-map/designer/%s' % self.project_id.id,
                'target': 'self',
            }

        return {'type': 'ir.actions.act_window_close'}