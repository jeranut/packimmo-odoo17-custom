# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    contract_foreign_currency_id = fields.Many2one(
        "res.currency",
        string="Devise contractuelle",
        compute="_compute_contract_foreign_price",
        readonly=True,
    )

    contract_foreign_price = fields.Monetary(
        string="Montant contractuel devise",
        currency_field="contract_foreign_currency_id",
        compute="_compute_contract_foreign_price",
        readonly=True,
    )

    contract_exchange_rate_label = fields.Char(
        string="Taux contractuel",
        compute="_compute_contract_foreign_price",
        readonly=True,
    )

    contract_foreign_amount_mga = fields.Monetary(
        string="Montant contractuel MGA",
        currency_field="company_currency_id",
        compute="_compute_contract_foreign_price",
        readonly=True,
    )

    @api.depends(
        "currency_id",
        "tenancy_id",
        "tenancy_property_id",
        "sold_property_id",
    )
    def _compute_contract_foreign_price(self):
        for move in self:
            move.contract_foreign_price = 0.0
            move.contract_foreign_currency_id = False
            move.contract_exchange_rate_label = False
            move.contract_foreign_amount_mga = 0.0

            property_rec = move.tenancy_property_id or move.sold_property_id

            if not property_rec:
                continue

            if "foreign_price" in property_rec._fields:
                move.contract_foreign_price = property_rec.foreign_price or 0.0

            if "foreign_currency_id" in property_rec._fields:
                move.contract_foreign_currency_id = property_rec.foreign_currency_id

            foreign_currency = move.contract_foreign_currency_id
            invoice_currency = move.currency_id
            company_currency = move.company_currency_id or move.company_id.currency_id

            if not (
                foreign_currency
                and invoice_currency
                and foreign_currency != invoice_currency
                and move.contract_foreign_price
            ):
                continue

            symbol = foreign_currency.symbol or foreign_currency.name
            tenancy = move.tenancy_id

            if (
                tenancy
                and "rent_exchange_mode" in tenancy._fields
                and tenancy.rent_exchange_mode == "fixed"
            ):
                fixed_rate = 0.0

                if "exchange_rate" in property_rec._fields:
                    fixed_rate = property_rec.exchange_rate or 0.0

                if fixed_rate:
                    move.contract_exchange_rate_label = (
                        "Taux fixe du contrat : 1 %s = %s %s"
                        % (
                            symbol,
                            "{:,.0f}".format(fixed_rate).replace(",", " "),
                            company_currency.name,
                        )
                    )

                continue

            rate = foreign_currency.rate or 0.0

            if not rate:
                continue

            rate_amount = 1.0 / rate

            move.contract_foreign_amount_mga = (
                move.contract_foreign_price * rate_amount
            )

            move.contract_exchange_rate_label = (
                "Dernier taux : 1 %s = %s %s"
                % (
                    symbol,
                    "{:,.0f}".format(rate_amount).replace(",", " "),
                    company_currency.name,
                )
            )

    def action_post(self):
        for move in self:
            if move.state != "draft":
                continue

            tenancy = move.tenancy_id

            if not tenancy:
                continue

            if "rent_exchange_mode" not in tenancy._fields:
                continue

            if tenancy.rent_exchange_mode != "mid":
                continue

            if not move.contract_foreign_amount_mga:
                continue

            first_line = move.invoice_line_ids[:1]

            if not first_line:
                continue

            price_unit = first_line.price_unit or 0.0
            contract_amount = move.contract_foreign_amount_mga or 0.0

            if abs(price_unit - contract_amount) > 1:
                first_line.write({
                    "price_unit": contract_amount,
                })

                move.message_post(
                    body=(
                        "Prix unitaire corrigé automatiquement avant validation.<br/>"
                        "Mode de conversion : Taux du MID<br/>"
                        "Ancien prix unitaire : %s Ar<br/>"
                        "Nouveau prix unitaire : %s Ar"
                        % (
                            "{:,.0f}".format(price_unit).replace(",", " "),
                            "{:,.0f}".format(contract_amount).replace(",", " "),
                        )
                    )
                )

        return super().action_post()