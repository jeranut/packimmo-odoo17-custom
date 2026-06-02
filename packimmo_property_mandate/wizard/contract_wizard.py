# -*- coding: utf-8 -*-

from odoo import api, models


class ContractWizard(models.TransientModel):
    _inherit = "contract.wizard"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")

        if active_model != "property.details" or not active_id:
            return res

        property_rec = self.env["property.details"].browse(active_id)

        mandate = property_rec.mandate_id

        if mandate and mandate.deposit_amount > 0:
            res.update({
                "is_any_deposit": True,
                "deposit_amount": mandate.deposit_amount,
            })

        return res