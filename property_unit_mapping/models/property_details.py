# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    map_polygon_json = fields.Text(string='Map Polygon JSON', copy=False)
    unit_map_line_id = fields.One2many('property.unit.map.line', 'property_id', string='Map Zone')
    map_color = fields.Char(string='Map Color', compute='_compute_map_color')
    unit_map_label_key = fields.Char(
        compute='_compute_unit_map_label_key',
        store=True,
        index=True,
        copy=False,
    )

    _sql_constraints = [
        (
            'subproject_unit_map_label_key_unique',
            'unique(subproject_id, unit_map_label_key)',
            'Cette référence plan existe déjà dans ce sous-projet.',
        ),
    ]

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

    @api.depends('unit_map_label')
    def _compute_unit_map_label_key(self):
        for rec in self:
            rec.unit_map_label_key = (
                ' '.join(rec.unit_map_label.split()).casefold()
                if rec.unit_map_label
                else False
            )

    @api.constrains('unit_map_label', 'subproject_id')
    def _check_unique_unit_map_label_per_subproject(self):
        for rec in self.filtered(lambda prop: prop.subproject_id and prop.unit_map_label):
            normalized_label = ' '.join(rec.unit_map_label.split()).casefold()
            other_properties = self.search([
                ('id', '!=', rec.id),
                ('subproject_id', '=', rec.subproject_id.id),
                ('unit_map_label', '!=', False),
            ])
            duplicate = other_properties.filtered(
                lambda prop: ' '.join(prop.unit_map_label.split()).casefold()
                == normalized_label
            )[:1]
            if duplicate:
                raise ValidationError(
                    _(
                        "La référence plan '%(label)s' existe déjà dans le sous-projet "
                        "'%(subproject)s'."
                    )
                    % {
                        'label': rec.unit_map_label,
                        'subproject': rec.subproject_id.display_name,
                    }
                )
