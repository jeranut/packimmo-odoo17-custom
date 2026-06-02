# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class PropertyDetails(models.Model):
    _inherit = "property.details"

    mandate_id = fields.Many2one(
        "property.mandate",
        string="Mandat",
        tracking=True,
        ondelete="set null",
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
            },
        }

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

            # Si le bien appartient à PACKIMMO
            # on autorise directement
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
