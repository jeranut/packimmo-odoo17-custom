# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TenancyDetails(models.Model):
    _inherit = "tenancy.details"

    habitation_contract_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Dernier contrat bail habitation",
        copy=False,
        readonly=True,
        tracking=True,
    )

    habitation_contract_date = fields.Datetime(
        string="Date impression bail habitation",
        copy=False,
        readonly=True,
        tracking=True,
    )

    rent_exchange_mode = fields.Selection(
        [
            ("fixed", "Taux fixe"),
            ("mid", "Taux du MID"),
        ],
        string="Mode de conversion",
        tracking=True,
    )

    fixed_exchange_rate = fields.Float(
        string="Taux fixe contrat",
        digits=(16, 6),
        tracking=True,
    )

    exchange_description = fields.Char(
        string="Conversion devises",
        compute="_compute_exchange_description",
    )

    rent_price_text = fields.Char(
        string="Loyer Ariary en lettres",
        compute="_compute_rent_price_text",
        tracking=True,
    )

    rent_foreign_price_text = fields.Char(
        string="Loyer devise en lettres",
        compute="_compute_rent_price_text",
        tracking=True,
    )

    @api.depends("rent_exchange_mode", "fixed_exchange_rate", "property_id")
    def _compute_exchange_description(self):
        for rec in self:
            currency = "devise"

            if rec.property_id:
                if (
                    "foreign_currency_id" in rec.property_id._fields
                    and rec.property_id.foreign_currency_id
                ):
                    currency = rec.property_id.foreign_currency_id.display_name
                elif (
                    "foreign_currency" in rec.property_id._fields
                    and rec.property_id.foreign_currency
                ):
                    currency = rec.property_id.foreign_currency.display_name

            if rec.rent_exchange_mode == "fixed":
                rate = "{:,.2f}".format(
                    rec.fixed_exchange_rate or 0.0
                ).replace(",", " ")

                rec.exchange_description = (
                    "Taux fixe : 1 %s = %s Ar" % (currency, rate)
                )

            elif rec.rent_exchange_mode == "mid":
                rec.exchange_description = (
                    "Taux du MID (taux de change dynamique)"
                )

            else:
                rec.exchange_description = False

    @api.depends("property_id", "property_id.price", "currency_id")
    def _compute_rent_price_text(self):
        for rec in self:
            rec.rent_price_text = ""
            rec.rent_foreign_price_text = ""

            property_rec = rec.property_id
            if not property_rec:
                continue

            if property_rec.price and rec.currency_id:
                rec.rent_price_text = rec.currency_id.amount_to_text(
                    property_rec.price
                )

            if (
                "foreign_price" in property_rec._fields
                and property_rec.foreign_price
                and "foreign_currency_id" in property_rec._fields
                and property_rec.foreign_currency_id
            ):
                rec.rent_foreign_price_text = (
                    property_rec.foreign_currency_id.amount_to_text(
                        property_rec.foreign_price
                    )
                )