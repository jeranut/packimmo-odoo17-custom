# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    meter_type = fields.Selection(
        [("water", "Eau"), ("electricity", "Électricité")],
        string="Type compteur",
        copy=False,
    )

    meter_fixed_fee_history_id = fields.Many2one(
        "syndic.meter.fixed.fee.history",
        string="Historique redevance",
        copy=False,
        ondelete="set null",
    )

    meter_total_fixed_fee_amount = fields.Monetary(
        string="Redevance totale",
        currency_field="currency_id",
        copy=False,
    )

    meter_fixed_fee_divisor_count = fields.Integer(
        string="Nombre de locataires",
        copy=False,
    )

    meter_fixed_fee_part_amount = fields.Monetary(
        string="Part redevance",
        currency_field="currency_id",
        copy=False,
    )

    meter_fixed_fee_label = fields.Char(
        string="Info redevance",
        compute="_compute_meter_fee_info",
        store=False,
    )

    @api.depends(
        "meter_type",
        "meter_total_fixed_fee_amount",
        "meter_fixed_fee_divisor_count",
        "meter_fixed_fee_part_amount",
    )
    def _compute_meter_fee_info(self):
        for move in self:
            if not move.meter_total_fixed_fee_amount or not move.meter_fixed_fee_divisor_count:
                move.meter_fixed_fee_label = False
                continue

            fee_label = "Redevance / taxe communale"
            if move.meter_type == "water":
                fee_label = "Redevance eau / taxe communale"
            elif move.meter_type == "electricity":
                fee_label = "Redevance électricité / taxe communale"

            move.meter_fixed_fee_label = (
                f"{fee_label} : "
                f"{move.meter_total_fixed_fee_amount:,.2f} Ar "
                f"÷ {move.meter_fixed_fee_divisor_count} locataires "
                f"= {move.meter_fixed_fee_part_amount:,.2f} Ar"
            )
