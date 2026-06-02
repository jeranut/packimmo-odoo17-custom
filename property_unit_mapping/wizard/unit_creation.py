# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class UnitCreation(models.TransientModel):
    _inherit = 'unit.creation'

    total_unit_to_create = fields.Integer(string='Total Units', compute='_compute_total_unit_to_create')
    has_multiple_unit_to_create = fields.Boolean(string='Multiple Units', compute='_compute_total_unit_to_create')

    @api.depends('total_floors', 'units_per_floor')
    def _compute_total_unit_to_create(self):
        for rec in self:
            total = (rec.total_floors or 0) * (rec.units_per_floor or 0)
            rec.total_unit_to_create = total
            rec.has_multiple_unit_to_create = total > 1

    def _get_active_project_for_map(self):
        active_id = self.env.context.get('active_id')
        unit_from = self.env.context.get('unit_from')
        if not active_id:
            raise UserError(_('No active project found.'))
        if unit_from == 'project':
            return self.env['property.project'].browse(active_id)
        if unit_from == 'sub_project':
            sub_project = self.env['property.sub.project'].browse(active_id)
            return sub_project.property_project_id
        raise UserError(_('The cartography must be opened from a project or sub-project.'))

    def action_import_unit_map_image(self):
        self.ensure_one()
        if self.total_unit_to_create <= 1:
            raise UserError(_('Cartography is available only when there is more than one unit.'))
        project = self._get_active_project_for_map()
        return {
            'name': _('Import Unit Map Image'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.unit.map.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': project.id,
                'default_total_floors': self.total_floors,
                'default_units_per_floor': self.units_per_floor,
            },
        }
