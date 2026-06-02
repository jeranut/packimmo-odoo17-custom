# -*- coding: utf-8 -*-
from odoo import fields, models


class TenancyDetails(models.Model):
    _inherit = "tenancy.details"

    syndic_share = fields.Float(
        string="Tantièmes syndic",
        required=True,
        default=0.0,
        help="Quote-part du lot utilisée pour la répartition des charges syndic.",
    )

    def create(self, vals_list):
        records = super().create(vals_list)
        records._packimmo_refresh_syndic_on_running_contract()
        return records

    def write(self, vals):
        res = super().write(vals)

        if {"contract_type", "syndic_share", "tenancy_id", "property_id"}.intersection(vals):
            self._packimmo_refresh_syndic_on_running_contract()

        return res

    def _packimmo_refresh_syndic_on_running_contract(self):
        for tenancy in self:
            if tenancy.contract_type != "running_contract":
                continue

            property_rec = tenancy.property_id
            if not property_rec:
                continue

            syndics = self.env["syndic.management"].search([
                "|",
                ("property_ids", "in", property_rec.id),
                "|",
                ("project_id", "=", property_rec.property_project_id.id if property_rec.property_project_id else False),
                ("subproject_id", "=", property_rec.subproject_id.id if property_rec.subproject_id else False),
            ])

            for syndic in syndics:
                syndic.action_refresh_properties()

                owner_lines = syndic.owner_line_ids.filtered(
                    lambda l: l.property_id.id == property_rec.id
                )
                owner_lines.write({
                    "tenant_id": tenancy.tenancy_id.id if tenancy.tenancy_id else False,
                    "share": tenancy.syndic_share,
                })

                charges = self.env["syndic.charge"].search([
                    ("syndic_id", "=", syndic.id),
                    ("state", "in", ["draft", "distributed"]),
                ])

                for charge in charges:
                    charge.action_distribute()
