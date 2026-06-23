# -*- coding: utf-8 -*-

from odoo import _, api, models


class PropertyVendor(models.Model):
    _inherit = "property.vendor"

    def _sync_packimmo_sale_workflow_inventory_stage(self):
        for sale_contract in self:
            if sale_contract.stage != "sold":
                continue

            property_record = sale_contract.property_id
            task = property_record.location_project_task_id if property_record else False
            if not task or task.project_id.name != "VENTE":
                continue

            target_stage = task._get_inventory_stage(task.project_id)
            if not target_stage or task.stage_id == target_stage:
                continue

            previous_stage_name = task.stage_id.display_name
            task.with_context(allow_visit_stage_transition=True).write({
                "stage_id": target_stage.id,
            })
            task.message_post(
                body=_(
                    "Vente confirmée <b>%s</b> : étape passée de "
                    "<b>%s</b> à <b>%s</b>."
                )
                % (
                    sale_contract.display_name,
                    previous_stage_name,
                    target_stage.display_name,
                )
            )

    def _sync_packimmo_morcellement_acte_vente_stage(self):
        for sale_contract in self:
            if sale_contract.stage != "sold" or not sale_contract.sale_invoice_ids:
                continue

            currency = sale_contract.currency_id or self.env.company.currency_id
            if not currency.is_zero(sale_contract.remaining_amount):
                continue

            property_record = sale_contract.property_id
            task = property_record.location_project_task_id if property_record else False
            if not task or task.project_id.name != "MORCELLEMENT":
                continue

            if not task._is_promise_sale_stage(task.stage_id):
                continue

            target_stage = task._get_acte_vente_stage(task.project_id)
            if not target_stage or task.stage_id == target_stage:
                continue

            previous_stage_name = task.stage_id.display_name
            task.with_context(allow_visit_stage_transition=True).write({
                "stage_id": target_stage.id,
            })
            task.message_post(
                body=_(
                    "Paiement complet sur <b>%s</b> : étape passée de "
                    "<b>%s</b> à <b>%s</b>."
                )
                % (
                    sale_contract.display_name,
                    previous_stage_name,
                    target_stage.display_name,
                )
            )

    def write(self, vals):
        res = super().write(vals)
        if vals.get("stage") == "sold":
            self._sync_packimmo_sale_workflow_inventory_stage()
        if {"stage", "sale_invoice_ids"} & set(vals):
            self._sync_packimmo_morcellement_acte_vente_stage()
        return res


class SaleInvoice(models.Model):
    _inherit = "sale.invoice"

    def _sync_packimmo_morcellement_acte_vente_stage(self):
        self.mapped("property_sold_id")._sync_packimmo_morcellement_acte_vente_stage()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_packimmo_morcellement_acte_vente_stage()
        return records

    def write(self, vals):
        res = super().write(vals)
        if {"amount", "tax_ids", "invoice_id", "property_sold_id"} & set(vals):
            self._sync_packimmo_morcellement_acte_vente_stage()
        return res

    def unlink(self):
        sale_contracts = self.mapped("property_sold_id")
        res = super().unlink()
        sale_contracts._sync_packimmo_morcellement_acte_vente_stage()
        return res


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        res = super().write(vals)
        if {"amount_residual", "payment_state", "state", "line_ids"} & set(vals):
            self.mapped("sold_id")._sync_packimmo_morcellement_acte_vente_stage()
        return res
