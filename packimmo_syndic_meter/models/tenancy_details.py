# -*- coding: utf-8 -*-
from odoo import models


class TenancyDetails(models.Model):
    _inherit = "tenancy.details"

    def write(self, vals):
        res = super().write(vals)

        if "contract_type" in vals or "tenancy_id" in vals or "property_id" in vals:
            self._packimmo_sync_meter_tenant()

        return res

    def _packimmo_sync_meter_tenant(self):
        for tenancy in self:
            if tenancy.contract_type != "running_contract":
                continue

            property_rec = tenancy.property_id
            tenant = tenancy.tenancy_id

            if not property_rec or not tenant:
                continue

            meters = self.env["syndic.meter"].search([
                ("property_id", "=", property_rec.id),
                ("active", "=", True),
            ])

            meters.write({
                "tenant_id": tenant.id,
                "active": True,
            })