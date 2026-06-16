# -*- coding: utf-8 -*-

from odoo import _, models


class ActiveContract(models.Model):
    _inherit = "active.contract"

    def action_create_contract(self):
        res = super().action_create_contract()

        for wizard in self:
            tenancy = wizard.contract_id
            property_record = tenancy.property_id
            task = property_record.location_project_task_id if property_record else False

            if not task or task.project_id.name != "LOCATION":
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
                    "Création/activation du contrat <b>%s</b> : étape passée de "
                    "<b>%s</b> à <b>%s</b>."
                )
                % (
                    tenancy.display_name,
                    previous_stage_name,
                    target_stage.display_name,
                )
            )

        return res
