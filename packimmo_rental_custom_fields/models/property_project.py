# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyProject(models.Model):
    _inherit = "property.project"

    property_type = fields.Selection(
        selection=[
            ("residential", "Résidentielle"),
            ("commercial", "Commerciale"),
            ("land", "Terrain"),
        ],
        string="Type de propriété",
    )

    property_land_name = fields.Char(
        string="Nom de la propriété",
        help="Exemple : TANJONA II",
    )

    property_title_number = fields.Char(
        string="Titre n°",
        help="Exemple : 6176-H",
    )

    
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        if "property_type" in res and "selection" in res["property_type"]:
            res["property_type"]["selection"] = [
                item for item in res["property_type"]["selection"]
                if item[0] != "industrial"
            ]
        return res

    @api.constrains(
        "property_type",
        "property_land_name",
        "property_title_number",
    )
    def _check_land_fields_required(self):

        for rec in self:

            if rec.property_type == "land":

                if not rec.property_land_name:
                    raise ValidationError(
                        _("Veuillez renseigner le nom de la propriété.")
                    )

                if not rec.property_title_number:
                    raise ValidationError(_("Veuillez renseigner le titre n°."))

    def _sync_region_city(self):
        for rec in self:
            if rec.region_id and rec.city_id and "city_ids" in rec.region_id._fields:
                if rec.city_id not in rec.region_id.city_ids:
                    rec.region_id.write({"city_ids": [(4, rec.city_id.id)]})

    @api.onchange("region_id", "city_id")
    def _onchange_region_city_sync(self):
        self._sync_region_city()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_region_city()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "region_id" in vals or "city_id" in vals:
            self._sync_region_city()
        return res
