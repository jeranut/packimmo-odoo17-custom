# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SyndicMeterFixedFeeHistory(models.Model):
    _name = "syndic.meter.fixed.fee.history"
    _description = "Historique redevance / taxe communale compteur"
    _order = "date_to desc, id desc"

    name = fields.Char(string="Libellé", compute="_compute_name", store=True)
    syndic_id = fields.Many2one(
        "syndic.management",
        string="Syndic",
        required=True,
        ondelete="cascade",
    )
    batch_id = fields.Many2one(
        "syndic.meter.reading.batch",
        string="Relevé",
        ondelete="set null",
    )
    meter_type = fields.Selection(
        [("water", "Eau"), ("electricity", "Électricité")],
        string="Type compteur",
        required=True,
    )
    date_from = fields.Date(string="Date début")
    date_to = fields.Date(string="Date fin")
    total_amount = fields.Monetary(string="Redevance totale", currency_field="currency_id")
    divisor_count = fields.Integer(string="Nombre de locataires")
    part_amount = fields.Monetary(string="Part par locataire", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        related="syndic_id.currency_id",
        store=True,
        readonly=True,
    )
    invoice_ids = fields.One2many(
        "account.move",
        "meter_fixed_fee_history_id",
        string="Factures",
    )
    invoice_count = fields.Integer(string="Nombre de factures", compute="_compute_invoice_count")

    @api.depends("invoice_ids")
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends("meter_type", "date_from", "date_to")
    def _compute_name(self):
        for rec in self:
            type_label = dict(rec._fields["meter_type"].selection).get(rec.meter_type, "")
            period = ""
            if rec.date_from and rec.date_to:
                period = "%s - %s" % (rec.date_from, rec.date_to)
            elif rec.date_to:
                period = str(rec.date_to)
            rec.name = "Redevance %s %s" % (type_label, period)
