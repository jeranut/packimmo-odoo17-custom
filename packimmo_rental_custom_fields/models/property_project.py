# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyProject(models.Model):
    _inherit = "property.project"
    _order = "date_of_project desc, id desc"

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

    project_sequence = fields.Char(
        default="New",
        required=False,
        readonly=True,
        copy=False,
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)
        if "property_type" in res and "selection" in res["property_type"]:
            res["property_type"]["selection"] = [
                item
                for item in res["property_type"]["selection"]
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

    def _get_project_sequence_prefix(self, property_type):
        return {
            "residential": "RES",
            "commercial": "COM",
            "land": "TER",
        }.get(property_type)

    def _get_project_sequence_code(self, property_type):
        return {
            "residential": "property.project.residential",
            "commercial": "property.project.commercial",
            "land": "property.project.land",
        }.get(property_type)

    def _get_project_sequence(self, property_type, sequence_date):
        sequence_code = self._get_project_sequence_code(property_type)
        if not sequence_code:
            return "New"

        sequence_date = fields.Date.to_date(sequence_date) or fields.Date.context_today(self)
        return (
            self.env["ir.sequence"].next_by_code(
                sequence_code,
                sequence_date=sequence_date,
            )
            or "New"
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            sequence = vals.get("project_sequence")
            if sequence and sequence not in ("New", "Nouveau"):
                continue

            vals["project_sequence"] = self._get_project_sequence(
                vals.get("property_type"),
                vals.get("date_of_project") or fields.Date.context_today(self),
            )

        records = super().create(vals_list)
        records._sync_region_city()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "region_id" in vals or "city_id" in vals:
            self._sync_region_city()
        return res

    @api.constrains("landlord_id")
    def _check_landlord_id_is_landlord(self):
        for rec in self:
            if rec.landlord_id and rec.landlord_id.user_type != "landlord":
                raise ValidationError(
                    _("Le propriétaire sélectionné doit être de type Propriétaire.")
                )

    @api.onchange("landlord_id")
    def _onchange_landlord_id_check_type(self):
        for rec in self:
            if rec.landlord_id and rec.landlord_id.user_type != "landlord":
                warning = {
                    "title": _("Propriétaire invalide"),
                    "message": _(
                        "Le contact sélectionné doit être de type Propriétaire."
                    ),
                }
                rec.landlord_id = False
                return {"warning": warning}
