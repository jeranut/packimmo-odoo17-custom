# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertySubProject(models.Model):
    _inherit = 'property.sub.project'

    land_phase_map_background = fields.Selection(
        related='property_project_id.land_phase_map_background',
        string='Fond de carte terrain',
        readonly=True,
    )

    def _is_land_subproject_for_phase(self):
        self.ensure_one()
        return getattr(self, 'property_type', False) == 'land'

    def action_open_unit_map_editor(self):
        self.ensure_one()
        if self._is_land_subproject_for_phase():
            self.action_prepare_unit_map_lines()
            return {
                'type': 'ir.actions.act_url',
                'url': '/property/land-phase/subproject/esri-designer/%s' % self.id,
                'target': 'new',
            }
        return super().action_open_unit_map_editor()

    def action_view_unit_map_website(self):
        self.ensure_one()
        if self._is_land_subproject_for_phase():
            return {
                'type': 'ir.actions.act_url',
                'url': '/property/land-phase/project/%s/map' % self.property_project_id.id,
                'target': 'new',
            }
        return super().action_view_unit_map_website()

    @api.depends(
        'property_type',
        'land_phase_map_background',
        'property_project_id.unit_map_image',
    )
    def _compute_unit_map_preview_html(self):
        super()._compute_unit_map_preview_html()
        for rec in self:
            if rec.id and rec.property_type == 'land':
                rec.unit_map_preview_html = '''
                    <div style="margin-top:8px; max-width:760px; border:1px solid #ddd; border-radius:8px; overflow:hidden; background:#fff;">
                        <iframe src="/property/land-phase/subproject/%s/preview" style="width:100%%; height:360px; border:0;"></iframe>
                    </div>
                ''' % rec.id
