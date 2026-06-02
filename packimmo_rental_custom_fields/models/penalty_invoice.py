# -*- coding: utf-8 -*-

from odoo import fields, models


class PenaltyInvoice(models.Model):
    _inherit = "penalty.invoice"

    cheque_reference = fields.Char(string="Référence chèque")
    observation = fields.Text(string="Observation")