# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyUnitMapLine(models.Model):
    _name = 'property.unit.map.line'
    _description = 'Property Unit Map Zone'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    project_id = fields.Many2one('property.project', string='Project', required=True, ondelete='cascade')
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
        related="property_id.property_project_id",
        string="Projet",
        store=True,
        readonly=True,
    )
    _sql_constraints = [
        (
            'project_subproject_property_unique',
            'unique(project_id, subproject_id, property_id)',
            'This property already has a map zone for this project/sub-project.'
        ),
    ]

    subproject_id = fields.Many2one(
        'property.sub.project',
        string='Sub Project',
        ondelete='cascade'
    )

    @api.constrains('project_id', 'property_id')
    def _check_project_property(self):
        for rec in self:
            if rec.property_id.property_project_id and rec.property_id.property_project_id != rec.project_id:
                raise ValidationError(_('The selected unit does not belong to this project.'))

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
