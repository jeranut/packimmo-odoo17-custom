# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class PropertyDetails(models.Model):
    _inherit = "property.details"
    _check_company_auto = True

    mandate_id = fields.Many2one(
        "property.mandate",
        string="Mandat",
        tracking=True,
        ondelete="set null",
        check_company=True,
    )

    mandate_type = fields.Selection(
        related="mandate_id.mandate_type",
        string="Type de mandat",
        store=True,
        readonly=True,
    )

    mandate_state = fields.Selection(
        related="mandate_id.state",
        string="État mandat",
        store=True,
        readonly=True,
    )

    mandate_exclusive = fields.Boolean(
        related="mandate_id.exclusive",
        string="Mandat exclusif",
        store=True,
        readonly=True,
    )

    mandate_end_date = fields.Date(
        related="mandate_id.end_date",
        string="Fin mandat",
        store=True,
        readonly=True,
    )
    has_simple_mandate = fields.Boolean(
        compute="_compute_has_simple_mandate",
    )
    property_subtype_category = fields.Selection(
        related="property_subtype_id.category",
        string="Catégorie sous-type",
        store=True,
    )
    is_company_property = fields.Boolean(
        string="Bien appartenant à la société",
        compute="_compute_is_company_property",
)
    @api.depends("landlord_id", "company_id")
    def _compute_is_company_property(self):
        for rec in self:
            rec.is_company_property = (
                rec.landlord_id
                and rec.company_id
                and rec.landlord_id.id == rec.company_id.partner_id.id
            )

    def action_open_mandate(self):
        self.ensure_one()

        if self.mandate_id:
            return {
                "type": "ir.actions.act_window",
                "name": "Mandat",
                "res_model": "property.mandate",
                "view_mode": "form",
                "res_id": self.mandate_id.id,
                "target": "current",
            }

        return {
            "type": "ir.actions.act_window",
            "name": "Nouveau mandat",
            "res_model": "property.mandate",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_owner_id": self.landlord_id.id if self.landlord_id else False,
                "default_operation_type": (
                    "rent" if self.sale_lease == "for_tenancy" else "sale"
                ),
                "default_property_ids": [(6, 0, [self.id])],
                "default_company_id": self.company_id.id,
            },
        }

    def action_open_contract_wizard_checked(self):
        for rec in self:
            if rec.mandate_type in ("simple", "exclusive") or rec.has_simple_mandate:
                raise ValidationError(
                    _(
                        "La création du contrat de bail n'est pas autorisée "
                        "pour un mandat simple ou exclusif."
                    )
                )

        return super().action_open_contract_wizard_checked()

    def _compute_has_simple_mandate(self):
        for rec in self:

            mandate = self.env["property.mandate"].search(
                [
                    ("property_ids", "in", rec.id),
                    ("state", "=", "active"),
                ],
                limit=1,
            )

            rec.has_simple_mandate = mandate.mandate_type == "simple"

    def action_in_available(self):
        for rec in self:

            is_land_morcellement = (
                rec.type == "land"
                and rec.property_subtype_id
                and rec.property_subtype_id.category == "morcellement"
            )

            # Cas terrain morcellement : pas besoin de mandat actif
            if is_land_morcellement:
                continue

            # Si le bien appartient à PACKIMMO : pas besoin de mandat actif
            if (
                rec.landlord_id
                and rec.company_id
                and rec.landlord_id.id == rec.company_id.partner_id.id
            ):
                continue

            mandate = self.env["property.mandate"].search(
                [
                    ("property_ids", "in", rec.id),
                    ("state", "=", "active"),
                ],
                limit=1,
            )

            if not mandate:
                raise UserError(
                    _(
                        "Veuillez créer un mandat actif pour valider la disponibilité du bien."
                    )
                )

        return super().action_in_available()
