# -*- coding: utf-8 -*-

from odoo import api, models


class BookingWizard(models.TransientModel):
    _inherit = "booking.wizard"

    @api.model
    def _get_mandate_customer_from_property(self, property_record):
        mandate = property_record.mandate_id if property_record else False
        return mandate.client_id if mandate and mandate.client_id else False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        property_record = self.env["property.details"].browse(
            res.get("property_id") or self.env.context.get("active_id")
        ).exists()
        customer = self._get_mandate_customer_from_property(property_record)
        if customer:
            res["customer_id"] = customer.id
        return res

    @api.onchange("property_id")
    def _onchange_property_id_set_mandate_customer(self):
        for wizard in self:
            customer = wizard._get_mandate_customer_from_property(wizard.property_id)
            if customer:
                wizard.customer_id = customer
