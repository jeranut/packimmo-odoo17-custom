# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PropertyProject(models.Model):
    _inherit = 'property.project'

    land_phase_map_background = fields.Selection(
        [
            ('esri', 'Fond satellite Esri'),
            ('image', 'Image de fond importée'),
        ],
        string='Fond de carte terrain',
        default='esri',
        required=True,
    )

    def _is_land_project_for_phase(self):
        self.ensure_one()
        return getattr(self, 'property_type', False) == 'land'

    def _has_land_subprojects(self):
        self.ensure_one()
        return bool(self.env['property.sub.project'].search_count([
            ('property_project_id', '=', self.id),
            ('property_type', '=', 'land'),
        ]))

    def action_open_unit_map_editor(self):
        self.ensure_one()
        if self._is_land_project_for_phase() and self._has_land_subprojects():
            return {
                'type': 'ir.actions.act_url',
                'url': '/property/land-phase/project/esri-designer/%s' % self.id,
                'target': 'new',
            }
        if self._is_land_project_for_phase() and self.land_phase_map_background == 'image':
            self.action_prepare_unit_map_lines()
            return {
                'type': 'ir.actions.act_url',
                'url': '/property/unit-map/designer/%s' % self.id,
                'target': 'new',
            }
        return super().action_open_unit_map_editor()

    def action_open_import_unit_map_wizard(self):
        self.ensure_one()
        if self._is_land_project_for_phase() and self.land_phase_map_background == 'image':
            return {
                'name': _('Importer une image de fond'),
                'type': 'ir.actions.act_window',
                'res_model': 'property.unit.map.import.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_project_id': self.id,
                    'land_phase_map_import': True,
                },
            }
        return super().action_open_import_unit_map_wizard()

    def action_view_unit_map_website(self):
        self.ensure_one()
        if self._is_land_project_for_phase():
            return {
                'type': 'ir.actions.act_url',
                'url': '/property/land-phase/project/%s/map?show_draft=1' % self.id,
                'target': 'new',
            }
        return super().action_view_unit_map_website()

    @api.depends('property_type', 'land_phase_map_background', 'unit_map_image')
    def _compute_unit_map_preview_html(self):
        super()._compute_unit_map_preview_html()
        for rec in self:
            if rec.id and rec.property_type == 'land':
                rec.unit_map_preview_html = '''
                    <div style="margin-top:8px; max-width:760px; border:1px solid #ddd; border-radius:8px; overflow:hidden; background:#fff;">
                        <iframe src="/property/land-phase/project/%s/preview" style="width:100%%; height:360px; border:0;"></iframe>
                    </div>
                ''' % rec.id
