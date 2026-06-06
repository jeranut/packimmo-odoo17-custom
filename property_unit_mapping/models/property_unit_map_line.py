# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyUnitMapLine(models.Model):
    _name = 'property.unit.map.line'
    _description = 'Property Unit Map Zone'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    property_id = fields.Many2one('property.details', string='Unit / Property', required=True, ondelete='cascade')
    property_seq = fields.Char(related='property_id.property_seq',string="Référence interne", store=True)
    stage = fields.Selection(related='property_id.stage', string='Status', store=True)
    color = fields.Char(related='property_id.map_color', string='Color')
    polygon_json = fields.Text(string='Polygon JSON', copy=False)
    note = fields.Char(string='Note')
    unit_map_label = fields.Char(
        related='property_id.unit_map_label',
        store=True,
        string='Réf plan'
    )

    project_id = fields.Many2one(
        'property.project',
        string='Projet',
        related='property_id.property_project_id',
        store=True,
        readonly=True,
    )
    subproject_id = fields.Many2one(
        'property.sub.project',
        string='Sub Project',
        ondelete='cascade'
    )
    _sql_constraints = [
    (
        'project_property_unique',
        'unique(project_id, property_id)',
        'This property already has a map zone in this project.'
    ),
]

    def write(self, vals):
        res = super().write(vals)
        if 'polygon_json' in vals:
            for rec in self:
                rec.property_id.map_polygon_json = rec.polygon_json
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.polygon_json:
                rec.property_id.map_polygon_json = rec.polygon_json
        return records
