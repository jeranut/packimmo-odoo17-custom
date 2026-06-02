# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    map_polygon_json = fields.Text(string='Map Polygon JSON', copy=False)
    unit_map_line_id = fields.One2many('property.unit.map.line', 'property_id', string='Map Zone')
    map_color = fields.Char(string='Map Color', compute='_compute_map_color')

    @api.depends('stage')
    def _compute_map_color(self):
        colors = {
            'draft': '#9ca3af',
            'available': '#22c55e',
            'booked': '#f59e0b',
            'sale': '#3b82f6',
            'sold': '#ef4444',
            'on_lease': '#8b5cf6',
        }
        for rec in self:
            rec.map_color = colors.get(rec.stage, '#6b7280')
