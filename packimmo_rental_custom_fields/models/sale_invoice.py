# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleInvoice(models.Model):
    _inherit = "sale.invoice"

    cheque_reference = fields.Char(string="Référence chèque")
    observation = fields.Text(string="Observation")

    @api.constrains("cheque_reference", "observation")
    def _check_cheque_reference_observation(self):
        for rec in self:
            if not rec.cheque_reference or not rec.observation:
                raise ValidationError(
                    _("Veuillez renseigner la référence chèque et l'observation.")
                )


class PropertyVendor(models.Model):
    _inherit = "property.vendor"

    contract_signature_date = fields.Date(
        string="Date de signature contrat",
    )

    def action_confirm_sale(self):
        for rec in self:
            if not rec.contract_signature_date:
                raise ValidationError(
                    _("Veuillez renseigner la date de signature du contrat.")
                )

            for line in rec.sale_invoice_ids:
                if not line.cheque_reference:
                    raise ValidationError(_("Veuillez renseigner la référence chèque."))

                if not line.observation:
                    raise ValidationError(_("Veuillez renseigner l'observation."))

        return super().action_confirm_sale()
