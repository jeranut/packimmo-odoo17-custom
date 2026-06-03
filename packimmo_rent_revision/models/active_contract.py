from odoo import models


class ActiveContract(models.Model):
    _inherit = "active.contract"

    def action_create_contract(self):
        res = super().action_create_contract()

        for wizard in self:
            if wizard.type == "manual" and wizard.contract_id:
                wizard.contract_id.action_apply_revision_on_manual_installments()

        return res