# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PropertySubProject(models.Model):
    _inherit = 'property.sub.project'

    unit_map_image = fields.Binary(string='Map Background Image', attachment=True)
    unit_map_image_name = fields.Char(string='Map Image Filename')
    phase_polygon_json = fields.Text(string="Phase Polygon")

    unit_map_line_ids = fields.One2many(
        'property.unit.map.line',
        'subproject_id',
        string='Unit Map Zones'
    )

    unit_count_for_map = fields.Integer(compute='_compute_unit_count_for_map')
    has_multiple_units = fields.Boolean(compute='_compute_unit_count_for_map')

    unit_map_preview_html = fields.Html(
        compute='_compute_unit_map_preview_html',
        sanitize=False
    )

    @api.depends('unit_map_line_ids', 'total_floors', 'units_per_floor')
    def _compute_unit_count_for_map(self):
        Property = self.env['property.details']

        for rec in self:
            count = Property.search_count([
                ('subproject_id', '=', rec.id)
            ])
            rec.unit_count_for_map = count
            rec.has_multiple_units = count > 1 or (rec.total_floors * rec.units_per_floor) > 1

    def action_open_import_unit_map_wizard(self):
        self.ensure_one()

        if self.property_type == 'land':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('Fond de carte Esri'),
                    'message': _('Pour un terrain, utilisez directement Dessiner la cartographie avec le fond de carte Esri.'),
                    'sticky': False,
                }
            }

        return {
            'name': _('Import Unit Map Image'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.unit.map.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subproject_id': self.id,
            },
        }

    def action_view_unit_map_website(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_url',
            'url': '/property/subproject/%s/unit-map' % self.id,
            'target': 'new',
        }

    def action_open_unit_map_editor(self):
        self.ensure_one()
        self.action_prepare_unit_map_lines()

        url = (
            '/property/subproject/unit-map/esri-designer/%s' % self.id
            if self.property_type == 'land'
            else '/property/subproject/unit-map/designer/%s' % self.id
        )

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_prepare_unit_map_lines(self):
        for subproject in self:
            properties = self.env['property.details'].search([
                ('subproject_id', '=', subproject.id)
            ])

            existing = set(subproject.unit_map_line_ids.mapped('property_id').ids)
            vals = []

            for prop in properties:
                if prop.id not in existing:
                    vals.append({
                        'project_id': subproject.property_project_id.id,
                        'subproject_id': subproject.id,
                        'property_id': prop.id,
                    })

            if vals:
                self.env['property.unit.map.line'].create(vals)

        return True

    @api.depends('unit_map_image', 'property_type')
    def _compute_unit_map_preview_html(self):
        for rec in self:
            if rec.id and rec.property_type == 'land':
                rec.unit_map_preview_html = '''
                    <div style="margin-top:8px; max-width:760px; border:1px solid #ddd; border-radius:8px; overflow:hidden; background:#fff;">
                        <iframe src="/property/subproject/unit-map/esri-preview/%s" style="width:100%%; height:360px; border:0;"></iframe>
                    </div>
                ''' % rec.id

            elif rec.id and rec.unit_map_image:
                rec.unit_map_preview_html = '''
                    <div style="margin-top:8px; max-width:760px; border:1px solid #ddd; border-radius:8px; overflow:hidden; background:#fff;">
                        <iframe src="/property/subproject/unit-map/preview/%s" style="width:100%%; height:360px; border:0;"></iframe>
                    </div>
                ''' % rec.id

            else:
                rec.unit_map_preview_html = '''
                    <div class="alert alert-info" style="margin-top:12px;">
                        Importez une image puis dessinez les unités du sous-projet.
                    </div>
                '''
