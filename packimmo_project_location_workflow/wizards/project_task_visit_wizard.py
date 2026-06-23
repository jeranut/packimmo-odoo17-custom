# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class ProjectTaskVisitWizard(models.TransientModel):
    _name = "project.task.visit.wizard"
    _description = "Planification visite bien immobilier"

    task_id = fields.Many2one(
        "project.task",
        string="Tâche",
        required=True,
        readonly=True,
    )

    visit_client_id = fields.Many2one(
        "res.partner",
        string="Client",
        domain=[("user_type", "=", "customer")],
        required=True,
    )

    visit_observation = fields.Text(
        string="Observation",
    )

    def action_confirm_visit(self):
        """Enregistre la visite, crée une sous-tâche et déplace la tâche vers VISITE."""
        self.ensure_one()

        visit_stage = self.task_id._get_visit_stage(self.task_id.project_id)

        if not visit_stage:
            raise UserError(_("L'étape VISITE est introuvable."))

        self.task_id.with_context(allow_visit_stage_transition=True).write({
            "visit_client_id": self.visit_client_id.id,
            "visit_observation": self.visit_observation,
            "stage_id": visit_stage.id,
        })

        self.env["project.task"].with_context(
            packimmo_allow_workflow_task_create=True
        ).create({
            "name": _("Visite - %s") % self.visit_client_id.display_name,
            "project_id": self.task_id.project_id.id,
            "company_id": self.task_id.company_id.id,
            "parent_id": self.task_id.id,
            "display_in_project": False,
            "visit_client_id": self.visit_client_id.id,
            "visit_observation": self.visit_observation,
            "user_ids": [(6, 0, self.task_id.user_ids.ids)],
        })

        return {"type": "ir.actions.act_window_close"}
